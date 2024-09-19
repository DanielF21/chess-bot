import torch
import torch.nn as nn
import torch.optim as optim
from load import create_data_loaders
from model import ChessCNN
import matplotlib.pyplot as plt
from tqdm.auto import tqdm
import time
from torch.cuda.amp import GradScaler, autocast
from google.cloud import storage
import io
import threading
from datetime import datetime
from io import StringIO

class TqdmToString(StringIO):
    def __init__(self):
        super().__init__()
        self.last_progress = ""

    def write(self, s):
        if s.strip():  # Only update if there's actual content
            self.last_progress = s.strip()

def save_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def save_model_to_gcs(model, bucket_name, destination_blob_name):
    """Saves a PyTorch model directly to GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Save model to a byte stream
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    buffer.seek(0)

    # Upload the model
    blob.upload_from_file(buffer, content_type='application/octet-stream')

    print(f"Model saved to gs://{bucket_name}/{destination_blob_name}")

def write_status(bucket_name, blob_name, tqdm_out):
    start_time = datetime.now()
    
    def update_status():
        while True:
            current_time = datetime.now()
            elapsed_time = (current_time - start_time).total_seconds() / 3600  # Convert to hours
            status = f"t + {elapsed_time:.2f} hours\n"
            status += f"Current progress: {tqdm_out.last_progress}\n"
            
            # Write to a local file
            with open("status.txt", "w") as f:
                f.write(status)
            
            # Upload to GCS
            save_to_gcs(bucket_name, "status.txt", blob_name)
            
            time.sleep(1800)  # Sleep for 30 minutes
    
    # Start the status update in a separate thread
    thread = threading.Thread(target=update_status)
    thread.daemon = True
    thread.start()

def train_model(num_epochs=50, batch_size=1024, learning_rate=0.001, data_file="dataset.txt"):
    train_loader, test_loader = create_data_loaders(data_file, batch_size=batch_size)

    # Initialize model, loss function, and optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ChessCNN().to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=5, verbose=True)
    train_losses = []
    test_losses = []

    best_test_loss = float('inf')
    patience = 10
    trigger_times = 0

    scaler = GradScaler()

    # Epochs to save the model (in case program crashes)
    save_epochs = {1, 2, 3, 5, 10, 15, 20, 25}

    tqdm_out = TqdmToString()
    # Start the status update
    write_status("daniel_chess", "status.txt", tqdm_out)

    start_time = time.time()
    last_update_time = start_time

    # Training
    for epoch in range(num_epochs):
        model.train()
        total_train_loss = 0
        epoch_start_time = time.time()

        train_pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs} [Train]", file=tqdm_out, dynamic_ncols=True)
        for inputs, labels in train_pbar:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()

            with autocast():
                outputs = model(inputs)
                loss = criterion(outputs, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            total_train_loss += loss.item()

            train_pbar.set_postfix({'loss': f'{loss.item():.4f}'})

        avg_train_loss = total_train_loss / len(train_loader)
        train_losses.append(avg_train_loss)

        # Validation
        model.eval()
        total_test_loss = 0
        test_pbar = tqdm(test_loader, desc=f"Epoch {epoch+1}/{num_epochs} [Valid]", file=tqdm_out, dynamic_ncols=True)
        with torch.no_grad():
            for inputs, labels in test_pbar:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                total_test_loss += loss.item()

                test_pbar.set_postfix({'loss': f'{loss.item():.4f}'})

        avg_test_loss = total_test_loss / len(test_loader)
        test_losses.append(avg_test_loss)

        scheduler.step(avg_test_loss)

        # Check for early stopping
        if avg_test_loss < best_test_loss:
            best_test_loss = avg_test_loss
            trigger_times = 0
            save_model_to_gcs(model, "daniel_chess", "best_chess_model.pth")
            print("New best model saved to GCS!")
        else:
            trigger_times += 1
            if trigger_times >= patience:
                print("Early stopping triggered.")
                break

        # Save the model at epochs save_epochs
        if (epoch + 1) in save_epochs:
            save_model_to_gcs(model, "daniel_chess", f"chess_model_epoch_{epoch + 1}.pth")
            print(f"Model saved to GCS at epoch {epoch + 1}.")

        # Check if 30 minutes have passed
        current_time = time.time()
        if current_time - last_update_time >= 1800:  # 1800 seconds = 30 minutes
            elapsed_hours = (current_time - start_time) / 3600
            status = f"t + {elapsed_hours:.2f} hours\n"
            status += f"Current progress: {tqdm_out.last_progress}\n"
            status += f"Epoch [{epoch+1}/{num_epochs}], Train Loss: {avg_train_loss:.4f}, Test Loss: {avg_test_loss:.4f}\n"
            
            with open("status.txt", "w") as f:
                f.write(status)
            save_to_gcs("daniel_chess", "status.txt", "status.txt")
            last_update_time = current_time

        epoch_end_time = time.time()
        epoch_duration = epoch_end_time - epoch_start_time

        print(f"Epoch [{epoch+1}/{num_epochs}], "
              f"Train Loss: {avg_train_loss:.4f}, "
              f"Test Loss: {avg_test_loss:.4f}, "
              f"Time: {epoch_duration:.2f}s")

    # Loss plot
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Training Loss')
    plt.plot(test_losses, label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.savefig('loss_plot.png')
    
    # Save to GCS
    save_to_gcs("daniel_chess", "loss_plot.png", "loss_plot.png")
    
    plt.close()

if __name__ == "__main__":
    train_model()