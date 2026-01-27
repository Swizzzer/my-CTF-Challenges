def predict_image_with_saved_model(
  img_path: str,
  model_path: str = "../src/models/anime_classifier_efficientnetv2m_best.pt",
  device: str | None = None,
  threshold: float = 0.5,
):
  import os
  from typing import Dict
  import torch
  import torch.nn as nn
  from PIL import Image
  from torchvision import transforms
  from torchvision.models import efficientnet_v2_m

  assert os.path.exists(model_path), f"ckpt 不存在：{model_path}"
  raw = torch.load(model_path, map_location="cpu")

  if (
    isinstance(raw, dict)
    and "state_dict" in raw
    and isinstance(raw["state_dict"], dict)
  ):
    state_dict = raw["state_dict"]
    meta_ckpt = raw
  elif isinstance(raw, dict):
    state_dict = raw
    meta_ckpt = {}
  else:
    raise RuntimeError("无法识别的 checkpoint 格式。")

  PREFIXES = ("module.", "model.", "_orig_mod.", "_forward_module.")

  def _strip_all_prefixes(k: str):
    changed = True
    while changed:
      changed = False
      for p in PREFIXES:
        if k.startswith(p):
          k = k[len(p) :]
          changed = True
    return k

  state_dict = {_strip_all_prefixes(k): v for k, v in state_dict.items()}
  keys = list(state_dict.keys())
  if "classifier.1.weight" in state_dict:
    fc_w_name = "classifier.1.weight"
  elif "classifier.0.weight" in state_dict:
    fc_w_name = "classifier.0.weight"
  else:
    cand = [k for k in keys if k.endswith(".weight")]
    cand.sort()
    fc_w_name = cand[-1]
  num_classes = state_dict[fc_w_name].shape[0]

  if device is None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
  model = efficientnet_v2_m(weights=None)
  in_features = model.classifier[-1].in_features
  model.classifier[-1] = nn.Linear(in_features, num_classes)

  model.load_state_dict(state_dict, strict=False)

  model.eval().to(device)
  model = model.to(memory_format=torch.channels_last)

  classes = (
    meta_ckpt.get("classes")
    or meta_ckpt.get("meta", {}).get("classes")
    or (
      ["positve", "negative"][:num_classes]
      if num_classes <= 2
      else [f"class_{i}" for i in range(num_classes)]
    )
  )
  pos_name = (
    meta_ckpt.get("positive_class_name")
    or meta_ckpt.get("meta", {}).get("positive_class_name")
    or next((c for c in classes if c.lower() != "negative"), classes[0])
  )
  if pos_name not in classes:
    classes = [pos_name] + [c for c in classes if c != pos_name]

  img_size = int(
    meta_ckpt.get("img_size") or meta_ckpt.get("meta", {}).get("img_size", 288)
  )

  IMAGENET_MEAN = (0.485, 0.456, 0.406)
  IMAGENET_STD = (0.229, 0.224, 0.225)
  eval_tfms = transforms.Compose(
    [
      transforms.Resize((img_size, img_size)),
      transforms.ToTensor(),
      transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ]
  )

  img = Image.open(img_path).convert("RGB")
  x = eval_tfms(img).unsqueeze(0).to(device, memory_format=torch.channels_last)
  with torch.no_grad(), torch.amp.autocast("cuda", enabled=(device == "cuda")):
    logits = model(x)
    probs = torch.softmax(logits, dim=1)[0].cpu().tolist()

  probs_dict: Dict[str, float] = {
    classes[i]: float(probs[i]) for i in range(len(classes))
  }
  pos_prob = probs_dict[pos_name]

  return bool(pos_prob >= threshold), pos_prob


if __name__ == "__main__":
  res, prob = predict_image_with_saved_model("./adv_submit.png")
  print(res, prob)
