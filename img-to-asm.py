#!/usr/bin/env python3
"""
Converte uma imagem PNG/JPG em dados .word RGB para o MIPS MARS.

Instalação:
    python -m pip install pillow

Exemplos:
    python imagem_para_mips.py cenario.png
    python imagem_para_mips.py cenario.png -o cenario.asm
    python imagem_para_mips.py cenario.png -o cenario.asm --width 64 --height 64
    python imagem_para_mips.py tela.png --label tela_inicial --width 128 --height 64
"""

import argparse
from pathlib import Path
from PIL import Image


def converter_imagem(entrada, saida, largura=None, altura=None, label="imagem",
                     pixels_por_linha=512, fundo="#000000"):
    imagem = Image.open(entrada).convert("RGBA")

    # Redimensiona se uma ou ambas as dimensões forem informadas.
    if largura is not None or altura is not None:
        nova_largura = largura if largura is not None else imagem.width
        nova_altura = altura if altura is not None else imagem.height
        imagem = imagem.resize(
            (nova_largura, nova_altura),
            Image.Resampling.NEAREST
        )

    # Bitmap Display usa uma cor por palavra. Como .word RGB não tem alpha,
    # pixels transparentes são mesclados com a cor de fundo escolhida.
    fundo_img = Image.new("RGB", imagem.size, fundo)
    fundo_img.paste(imagem, mask=imagem.getchannel("A"))
    imagem = fundo_img

    largura_final, altura_final = imagem.size
    pixels = list(imagem.getdata())

    linhas = [
        "# Dados de imagem gerados automaticamente",
        f"# Arquivo de origem: {Path(entrada).name}",
        f"# Dimensoes: {largura_final} x {altura_final}",
        f"# Total de pixels: {largura_final * altura_final}",
        ".data",
        f"{label}:",
    ]

    for inicio in range(0, len(pixels), pixels_por_linha):
        grupo = pixels[inicio:inicio + pixels_por_linha]
        valores = []
        for r, g, b in grupo:
            rgb = (r << 16) | (g << 8) | b
            valores.append(f"0x{rgb:08X}")
        linhas.append("    .word " + ", ".join(valores))

    linhas += [
        "",
        "# Para desenhar, percorra os pixels em ordem:",
        f"# quantidade de pixels = {largura_final * altura_final}",
        f"# largura = {largura_final}; altura = {altura_final}",
        "",
    ]

    Path(saida).write_text("\n".join(linhas), encoding="utf-8")
    return largura_final, altura_final, len(pixels)


def main():
    parser = argparse.ArgumentParser(
        description="Converte uma imagem em instrucoes .word RGB para o MIPS MARS."
    )
    parser.add_argument("imagem", help="Caminho da imagem de entrada (PNG, JPG etc.)")
    parser.add_argument("-o", "--saida", help="Arquivo .asm de saída")
    parser.add_argument("--width", type=int, help="Largura desejada em pixels")
    parser.add_argument("--height", type=int, help="Altura desejada em pixels")
    parser.add_argument("--label", default="imagem", help="Nome do rótulo Assembly (padrão: imagem)")
    parser.add_argument("--por-linha", type=int, default=8, help="Quantidade de cores por linha .word")
    parser.add_argument("--fundo", default="#000000", help="Cor para transparência, em hexadecimal, ex.: #000000")

    args = parser.parse_args()

    if args.width is not None and args.width <= 0:
        parser.error("--width precisa ser maior que zero")
    if args.height is not None and args.height <= 0:
        parser.error("--height precisa ser maior que zero")
    if args.por_linha <= 0:
        parser.error("--por-linha precisa ser maior que zero")
    if not args.label.replace("_", "a").isalnum() or args.label[0].isdigit():
        parser.error("--label precisa ser um nome válido de rótulo Assembly")
    if len(args.fundo) != 7 or not args.fundo.startswith("#"):
        parser.error("--fundo deve estar no formato #RRGGBB")

    try:
        int(args.fundo[1:], 16)
    except ValueError:
        parser.error("--fundo deve conter dígitos hexadecimais, como #000000")

    entrada = Path(args.imagem)
    if not entrada.is_file():
        parser.error(f"Imagem não encontrada: {entrada}")

    saida = Path(args.saida) if args.saida else entrada.with_suffix(".asm")

    try:
        largura, altura, total = converter_imagem(
            entrada=entrada,
            saida=saida,
            largura=args.width,
            altura=args.height,
            label=args.label,
            pixels_por_linha=args.por_linha,
            fundo=args.fundo,
        )
    except Exception as erro:
        parser.error(f"Não foi possível converter a imagem: {erro}")

    print("Conversão concluída!")
    print(f"Imagem: {entrada}")
    print(f"Saída:  {saida}")
    print(f"Dimensões: {largura} x {altura}")
    print(f"Pixels convertidos: {total}")
    print("Cores no formato RGB 0x00RRGGBB.")


if __name__ == "__main__":
    main()
