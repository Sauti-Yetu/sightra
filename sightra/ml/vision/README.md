# Sightra YOLO26 vision training

Production inference uses `sightra/models/weights/yolo26n.pt` (COCO-pretrained YOLO26n).

## Setup

```bash
pip install -r ../../requirements.txt
python download_datasets.py   # coco128 for train/val smoke tests
```

## Validate pretrained weights

```bash
python validate.py --device cpu
```

## Fine-tune (mobility classes)

```bash
python train.py --data data/sightra_mobility.yaml --classes 0,1,2,3,5,7,56,57,60 --epochs 30
```

Best weights are copied to `sightra/models/weights/sightra_yolo26n.pt`. Set:

```env
YOLO_MODEL_PATH=models/weights/sightra_yolo26n.pt
```

## Full COCO

Use `data/coco.yaml` and download COCO train2017/val2017 per [Ultralytics COCO docs](https://docs.ultralytics.com/datasets/detect/coco/). Not bundled in git due to size.
