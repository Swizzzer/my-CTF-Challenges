import numpy as np
import matplotlib.pyplot as plt
import json
from PIL import Image
import sys
import os
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torchvision
from torchvision import models
import torchvision.datasets as dsets
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, Dataset
from torchvision.utils import save_image

img_paths = sys.argv[1:]

class ImageDataset(Dataset):
    def __init__(self, paths, transform=None):
        self.paths = paths
        self.transform = transform

    def __getitem__(self, index):
        try:
            img = Image.open(img_paths[index]).convert('RGB')
            if(self.transform): img = self.transform(img)
            return img_paths[index], img

        except (OSError) as e:
            print(f"{img_paths}: {e}")
            return None

    def __len__(self):
        return len(self.paths)

batch_size = 10
img_transform =  transforms.Compose([
        transforms.Resize([224,224]),
        transforms.ToTensor()
])
image_dataset= ImageDataset(img_paths, img_transform)
image_dataloader = DataLoader(image_dataset,batch_size=batch_size,shuffle=False,drop_last=False)

device = "cpu"
model_path='./model_best.pth'

model = torchvision.models.resnet50()

load = torch.load(model_path,weights_only=True,map_location="cpu")
state_dict = load['model']
num_ftrs = model.fc.in_features  
model.fc = torch.nn.Linear(num_ftrs, 2)
model.load_state_dict(state_dict)

model = model.to(device)
model.eval()

def getimage(image_dataloader):
    for paths, images in image_dataloader:
        return images

from torchattacks import OnePixel
from torchattacks import PGD

images = getimage(image_dataloader)
images = images.to(device)
labels = torch.tensor([1])
labels = labels.to(device)

atk = PGD(model, eps=1/255, alpha=0.5/225, steps=10, random_start=True)
print(atk)

adv_images = atk(images, labels)

def get_pred(model, images, device):
    images = images.to(device)
    outputs = model(images)
    pred = outputs.argmax(dim=1)
    return pred

def imshow(img, title):
    denorm_img=img
    
    # 生成图像网格并转换为numpy数组
    grid = torchvision.utils.make_grid(denorm_img, nrow=1)  # 单行排列
    npimg = grid.cpu().numpy()
    
    # 调整维度顺序为 (高度, 宽度, 通道)
    npimg = np.transpose(npimg, (1, 2, 0))  # 关键修复步骤
    
    # 缩放像素值到 [0,255]
    npimg = (npimg * 255).clip(0, 255).astype(np.uint8)
    
    # 显示图像
    plt.figure(figsize=(5, 15))
    plt.imshow(npimg)
    plt.title(title)
    plt.axis('off')
    plt.show()
    
    # 保存图像 (修复后的保存方式)
    Image.fromarray(npimg).save("./atk.png")
    
idx = 0
pre = get_pred(model, adv_images[idx:idx+1], device)
imshow(adv_images[idx:idx+1], title="True:%d, Pre:%d"%(labels[idx], pre))