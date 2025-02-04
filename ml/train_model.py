import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import transforms, datasets, models
import torch.nn.functional as F
import kagglehub

def main():
    # 1. Download the ALL-IDB dataset from KaggleHub
    dataset_path = kagglehub.dataset_download("sizlingdhairya1/all-idb-images")
    print("Path to dataset files:", dataset_path)

    # 2. Define Data Transformations
    train_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225])
    ])

    val_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225])
    ])

    # 3. Check Dataset Structure and Create Datasets
    train_dir_candidate = os.path.join(dataset_path, "ALL-IDB1")
    val_dir_candidate   = os.path.join(dataset_path, "ALL-IDB2")

    if os.path.isdir(train_dir_candidate) and os.path.isdir(val_dir_candidate):
        print("Found subdirectories 'ALL-IDB1' and 'ALL-IDB2'.")
        train_dataset = datasets.ImageFolder(train_dir_candidate, transform=train_transforms)
        val_dataset   = datasets.ImageFolder(val_dir_candidate, transform=val_transforms)
    else:
        print("Subdirectories not found. Assuming dataset is a single folder; splitting data randomly.")
        full_dataset = datasets.ImageFolder(dataset_path, transform=train_transforms)
        total_size = len(full_dataset)
        train_size = int(0.8 * total_size)
        val_size   = total_size - train_size
        train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    print(f"Number of training images: {len(train_dataset)}")
    print(f"Number of validation images: {len(val_dataset)}")

    # 4. Create DataLoaders with num_workers=0 for stability
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
    val_loader   = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)

    # 5. Set Up the Model for Fine-Tuning
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = models.resnet18(pretrained=True)
    num_features = model.fc.in_features

    if hasattr(train_dataset, 'dataset'):
        num_classes = len(train_dataset.dataset.classes)
    else:
        num_classes = len(train_dataset.classes)
    model.fc = nn.Linear(num_features, num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)

    # 6. Training and Validation Loop
    num_epochs = 10
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        running_corrects = 0

        for inputs, labels in train_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

        epoch_loss = running_loss / len(train_dataset)
        epoch_acc = running_corrects.double() / len(train_dataset)
        print(f"Epoch {epoch+1}/{num_epochs} - Loss: {epoch_loss:.4f}, Acc: {epoch_acc:.4f}")

        model.eval()
        val_running_loss = 0.0
        val_running_corrects = 0

        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)

                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                loss = criterion(outputs, labels)

                val_running_loss += loss.item() * inputs.size(0)
                val_running_corrects += torch.sum(preds == labels.data)

        val_loss = val_running_loss / len(val_dataset)
        val_acc = val_running_corrects.double() / len(val_dataset)
        print(f"Validation - Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")

    # 7. Save the Fine-Tuned Model
    torch.save(model.state_dict(), "fine_tuned_resnet18.pth")
    print("Fine-tuned model saved to fine_tuned_resnet18.pth")

if __name__ == '__main__':
    main()
