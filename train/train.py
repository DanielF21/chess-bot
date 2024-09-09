import torch
import torch.nn as nn
import torch.optim as optim
from load import create_data_loaders
from model import ChessCNN
import matplotlib.pyplot as plt
from tqdm import tqdm
import time
from torch.cuda.amp import GradScaler, autocast

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

    # Epochs to save the model
    save_epochs = {1, 2, 3, 5, 10, 15, 20, 25}

    # Training
    for epoch in range(num_epochs):
        model.train()
        total_train_loss = 0
        epoch_start_time = time.time()

        train_pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs} [Train]")
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
        test_pbar = tqdm(test_loader, desc=f"Epoch {epoch+1}/{num_epochs} [Valid]")
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
            torch.save(model.state_dict(), "best_chess_model.pth")
            print("New best model saved!")
        else:
            trigger_times += 1
            if trigger_times >= patience:
                print("Early stopping triggered.")
                break

        # Save the model at specified epochs
        if (epoch + 1) in save_epochs:
            torch.save(model.state_dict(), f"chess_model_epoch_{epoch + 1}.pth")
            print(f"Model saved at epoch {epoch + 1}.")

        epoch_end_time = time.time()
        epoch_duration = epoch_end_time - epoch_start_time

        print(f"Epoch [{epoch+1}/{num_epochs}], "
              f"Train Loss: {avg_train_loss:.4f}, "
              f"Test Loss: {avg_test_loss:.4f}, "
              f"Time: {epoch_duration:.2f}s")

    # Plot loss
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Training Loss')
    plt.plot(test_losses, label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.savefig('loss_plot.png')
    plt.close()

if __name__ == "__main__":
    train_model()