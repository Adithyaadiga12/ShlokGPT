"""
generate.py

Generate Sanskrit text using a trained ShlokGPT model.

Example:
python generate.py \
    --checkpoint checkpoints/best.pt \
    --tokenizer tokenizer.model \
    --prompt "धर्मक्षेत्रे कुरुक्षेत्रे" \
    --max_new_tokens 200 \
    --temperature 0.8 \
    --top_k 40
"""
#C:\Adithya\ShlokGPT\ckpt_init.pt
import argparse

import sentencepiece as spm
import torch

from model import GPT, GPTConfig


def load_model(checkpoint_path, device):
    checkpoint = torch.load(checkpoint_path, map_location=device)

    # config
    if "config" in checkpoint:
        cfg = GPTConfig(**checkpoint["config"])
    else:
        cfg = GPTConfig()

    model = GPT(cfg)

    # state dict
    if "model" in checkpoint:
        model.load_state_dict(checkpoint["model"])
    elif "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.eval()
    model.to(device)

    return model, cfg


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Path to checkpoint",
    )

    parser.add_argument(
        "--tokenizer",
        required=True,
        help="SentencePiece model",
    )

    parser.add_argument(
        "--prompt",
        default="",
        help="Prompt",
    )

    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=200,
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.8,
    )

    parser.add_argument(
        "--top_k",
        type=int,
        default=40,
    )

    args = parser.parse_args()

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(f"Using device: {device}")

    ###############################
    # tokenizer
    ###############################

    sp = spm.SentencePieceProcessor()
    sp.load(args.tokenizer)

    ###############################
    # model
    ###############################

    model, cfg = load_model(args.checkpoint, device)

    print(f"Loaded model ({model.num_params()/1e6:.2f}M params)")

    ###############################
    # encode prompt
    ###############################

    if args.prompt.strip() == "":
        input_ids = [sp.bos_id()]
    else:
        input_ids = sp.encode(args.prompt)

    x = torch.tensor(
        [input_ids],
        dtype=torch.long,
        device=device,
    )

    ###############################
    # generate
    ###############################

    with torch.no_grad():

        y = model.generate(
            x,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
        )

    ###############################
    # decode
    ###############################

    output_ids = y[0].tolist()

    text = sp.decode(output_ids)

    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


if __name__ == "__main__":
    main()