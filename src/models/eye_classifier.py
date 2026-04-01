from pathlib import Path
from typing import Tuple

import torch
from torch import nn
from torchvision import models, transforms
from PIL import Image


class EyeStateModel(nn.Module):
    """
    Лёгкая модель на базе ResNet-18 для детекции состояния глаза (открыт/закрыт).
    """

    def __init__(self, pretrained: bool = False) -> None:
        super().__init__()
        # torchvision >= 0.13: параметр pretrained заменён на weights
        if pretrained:
            # Можно заменить на ResNet18_Weights.DEFAULT при необходимости
            backbone = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        else:
            backbone = models.resnet18(weights=None)
        in_features = backbone.fc.in_features
        backbone.fc = nn.Linear(in_features, 2)
        self.backbone = backbone

    def forward(self, x):  # type: ignore[override]
        return self.backbone(x)


class EyeStateClassifier:
    def __init__(self, weights_path: Path | None = None, device: str | None = None) -> None:
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = EyeStateModel(pretrained=False).to(self.device)
        self.model.eval()

        if weights_path is not None and weights_path.exists():
            state = torch.load(weights_path, map_location=self.device)
            self.model.load_state_dict(state)

        self.transform = transforms.Compose(
            [
                transforms.Resize((64, 64)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
            ]
        )

    @torch.inference_mode()
    def predict_open_prob(self, pil_img: Image.Image) -> float:
        """
        :return: вероятность того, что глаз ОТКРЫТ (класс 1).
        """
        img = pil_img.convert("RGB")
        tensor = self.transform(img).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1)
        return float(probs[0, 1].item())

    @torch.inference_mode()
    def predict_label(self, pil_img: Image.Image) -> Tuple[int, float]:
        prob_open = self.predict_open_prob(pil_img)
        label = 1 if prob_open >= 0.5 else 0
        return label, prob_open

