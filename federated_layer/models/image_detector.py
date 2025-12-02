"""
image_detector.py

Model definition for the best-performing image detector in the HealChain framework.
Selected Model: ResNet50 (Adapted for Grayscale)
Performance: ~99% Accuracy (Reference: Figure 6.1, HealChain Report)

This module adapts the standard ResNet50 architecture to accept 
1-channel grayscale X-ray inputs instead of standard 3-channel RGB.
"""

import torch
import torch.nn as nn
from torchvision import models

class ResNet50Gray(nn.Module):
    """
    ResNet50 adapted for 1-channel Grayscale input.
    
    Architecture Changes:
    1. Input Layer: Conv2d(3, 64) -> Conv2d(1, 64). 
       Weights are summed/averaged from pretrained RGB to preserve feature detection.
    2. Output Layer: Linear(2048, 1000) -> Linear(2048, num_classes).
    """
    def __init__(self, num_classes: int = 2, pretrained: bool = False):
        """
        Args:
            num_classes (int): Number of output classes (Default 2: Normal vs Pneumonia).
            pretrained (bool): If True, loads ImageNet weights (recommended for faster convergence).
        """
        super(ResNet50Gray, self).__init__()
        
        # Load standard ResNet50 architecture
        # Note: Using V1 is standard in PyTorch; aligns with V2 performance profile in this context.
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        self.resnet = models.resnet50(weights=weights)
        
        # --- Adaptation 1: Handle Grayscale Input (1 Channel) ---
        # Standard ResNet expects 3 channels (RGB). We modify the first layer.
        original_conv1 = self.resnet.conv1
        
        # Create new layer: 1 input channel, same output (64), same kernel/stride/padding
        new_conv1 = nn.Conv2d(
            in_channels=1, 
            out_channels=original_conv1.out_channels, 
            kernel_size=original_conv1.kernel_size, 
            stride=original_conv1.stride, 
            padding=original_conv1.padding, 
            bias=original_conv1.bias
        )
        
        # Weight Initialization:
        # If pretrained, average the RGB weights into a single channel to keep edge detection filters.
        # w_new = (w_R + w_G + w_B) / 3
        with torch.no_grad():
            if pretrained and original_conv1.weight is not None:
                new_conv1.weight[:] = torch.sum(original_conv1.weight, dim=1, keepdim=True) / 3.0
            elif original_conv1.weight is not None:
                # If not pretrained, just copy sum or let standard init handle it. 
                # Here we strictly mimic structure.
                pass
        
        self.resnet.conv1 = new_conv1
        
        # --- Adaptation 2: Classification Head ---
        # Replace the final 1000-class layer with specific num_classes (2 for Binary)
        num_ftrs = self.resnet.fc.in_features  # 2048 for ResNet50
        self.resnet.fc = nn.Linear(num_ftrs, num_classes)

    def forward(self, x):
        return self.resnet(x)

def get_best_model(num_classes: int = 2):
    """Factory function to retrieve the best performing model instance."""
    return ResNet50Gray(num_classes=num_classes)

if __name__ == "__main__":
    # Sanity Check
    print("Initializing Best Performing Model (ResNet50Gray)...")
    model = get_best_model()
    
    # Create dummy grayscale input [Batch, Channels, Height, Width]
    # Report specifies 200x200 images 
    dummy_input = torch.randn(1, 1, 200, 200) 
    
    try:
        output = model(dummy_input)
        print(f"✅ Model Forward Pass Successful.")
        print(f"   Input Shape: {dummy_input.shape}")
        print(f"   Output Shape: {output.shape} (Expected: [1, 2])")
    except Exception as e:
        print(f"❌ Model Failed: {e}")