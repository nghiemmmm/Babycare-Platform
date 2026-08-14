# -*- coding: utf-8 -*-
"""
Standalone Infant Cry Inference Script
Usage:
    python inference.py --audio_path "path/to/baby_cry.wav"
"""

import os
import sys
import csv
import argparse
import json
import numpy as np
import torch
import torchaudio

try:
    torchaudio.set_audio_backend("soundfile")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from models.ast_models import ASTModel


import soundfile as sf

def load_audio(wav_name):
    """Tải tệp âm thanh an toàn bằng soundfile hoặc torchaudio fallback."""
    try:
        data, sr = sf.read(wav_name)
        waveform = torch.from_numpy(data).float()
        if waveform.ndim == 1:
            waveform = waveform.unsqueeze(0)
        else:
            waveform = waveform.t()
        return waveform, sr
    except Exception:
        waveform, sr = torchaudio.load(wav_name)
        return waveform, sr


def make_features(wav_name, mel_bins=128, target_length=704):
    waveform, sr = load_audio(wav_name)
    
    # Resample to 16 kHz if necessary
    if sr != 16000:
        waveform = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)(waveform)
        sr = 16000
        
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
        
    # Padding audio ngắn dưới 1 giây (16,000 mẫu) để tránh lỗi spectrogram
    min_samples = 16000
    if waveform.shape[1] < min_samples:
        pad_size = min_samples - waveform.shape[1]
        waveform = torch.nn.functional.pad(waveform, (0, pad_size))

    fbank = torchaudio.compliance.kaldi.fbank(
        waveform,
        htk_compat=True,
        sample_frequency=sr,
        use_energy=False,
        window_type='hanning',
        num_mel_bins=mel_bins,
        dither=0.0,
        frame_shift=10
    )

    n_frames = fbank.shape[0]
    p = target_length - n_frames

    if p > 0:
        fbank = torch.nn.functional.pad(fbank, (0, 0, 0, p))
    elif p < 0:
        fbank = fbank[:target_length, :]

    # Spectrogram Normalization
    fbank = (fbank - (-4.2677393)) / (4.5689974 * 2)
    return fbank


def load_label(label_csv):
    with open(label_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',')
        lines = list(reader)
    labels = []
    ids = []  
    for i1 in range(1, len(lines)):
        id_str = lines[i1][1]
        label = lines[i1][2]
        ids.append(id_str)
        labels.append(label)
    return labels


# ---------------------------------------------------------------------------
# Module-level AST Model Singleton
# ---------------------------------------------------------------------------

class _ASTModelSingleton:
    """Giữ AST model đã load sẵn trong bộ nhớ, tránh torch.load() mỗi request."""

    def __init__(self):
        self.model = None
        self.labels = None
        self.device = None
        self._loaded = False

    def load(self, label_csv=None, checkpoint_path=None):
        """Load model và labels từ disk. Chỉ gọi 1 lần khi startup."""
        if self._loaded:
            return

        if label_csv is None:
            label_csv = os.path.join(BASE_DIR, 'data', 'esc_class_labels_indices.csv')
        if checkpoint_path is None:
            checkpoint_path = os.path.join(BASE_DIR, 'weights', 'best_audio_model.pth')

        if not os.path.exists(label_csv):
            raise FileNotFoundError(f"Label file not found: {label_csv}")
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Model checkpoint file not found: {checkpoint_path}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.labels = load_label(label_csv)
        n_class = len(self.labels)

        ast_mdl = ASTModel(
            label_dim=n_class,
            input_fdim=128,
            input_tdim=704,
            fstride=10,
            tstride=10,
            imagenet_pretrain=False,
            audioset_pretrain=False,
            verbose=False
        ).to(self.device)

        ckpt = torch.load(checkpoint_path, map_location=self.device)
        new_state = {k[7:] if k.startswith("module.") else k: v for k, v in ckpt.items()}
        ast_mdl.load_state_dict(new_state)
        ast_mdl.eval()

        self.model = ast_mdl
        self._loaded = True

    def clear(self):
        """Giải phóng model khỏi RAM/VRAM khi shutdown."""
        self.model = None
        self.labels = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded


# Singleton instance — được load 1 lần trong lifespan startup
_ast_singleton = _ASTModelSingleton()


def get_ast_model() -> _ASTModelSingleton:
    """Trả về singleton AST model. Tự load nếu chưa được load (fallback cho CLI)."""
    if not _ast_singleton.is_loaded:
        _ast_singleton.load()
    return _ast_singleton


def inference(audio_path, label_csv=None, checkpoint_path=None, _model_singleton=None):
    """
    Chạy inference phân loại tiếng khóc.

    Khi chạy trong FastAPI: _model_singleton được inject từ singleton đã load sẵn.
    Khi chạy từ CLI (if __name__ == '__main__'): tự load model lần đầu.

    Args:
        audio_path: Đường dẫn file audio.
        label_csv: Đường dẫn file label CSV (tùy chọn, mặc định tự tìm).
        checkpoint_path: Đường dẫn file weights .pth (tùy chọn, mặc định tự tìm).
        _model_singleton: Instance _ASTModelSingleton đã load. Nếu None, tự lấy singleton.

    Returns:
        dict với keys: label, confidence, scores, duration, model_version.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Lấy singleton (hoặc load nếu chạy từ CLI)
    singleton = _model_singleton or get_ast_model()
    device = singleton.device
    labels = singleton.labels
    ast_mdl = singleton.model

    # Load audio và calculate duration
    waveform, sr = load_audio(audio_path)
    duration = round(waveform.shape[1] / sr, 2)

    # Extract features
    feats = make_features(audio_path, mel_bins=128, target_length=704)
    feats = feats.unsqueeze(0).to(device)

    # Model Inference — không load lại model
    with torch.no_grad():
        output = torch.sigmoid(ast_mdl(feats))

    result = output.cpu().numpy()[0]
    sorted_idx = np.argsort(result)[::-1]

    scores = {labels[i]: round(float(result[i]), 4) for i in range(len(labels))}
    top_label = labels[sorted_idx[0]]
    confidence = round(float(result[sorted_idx[0]]), 4)

    return {
        "label": top_label,
        "confidence": confidence,
        "scores": scores,
        "duration": duration,
        "model_version": "AST base384 (Infant Cry Fine-tuned)"
    }



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Infant Cry Classification Inference")
    parser.add_argument("--audio_path", type=str, required=True, help="Path to input audio .wav file")
    args = parser.parse_args()

    res = inference(args.audio_path)
    print(json.dumps(res, indent=2, ensure_ascii=False))
