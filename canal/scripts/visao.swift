// Visão do Mac (framework Vision), sem internet e sem custo.
//   canal-visao rostos <img> [<img> ...]   -> JSON com os rostos de cada imagem
//                                            (x, y, w, h normalizados, origem no canto de cima à esquerda)
//   canal-visao recorte <entrada> <saida.png> -> PNG com fundo transparente, justo na pessoa
//                                               (o mesmo "copiar sujeito" das Fotos)
// O canal.py compila este arquivo em ~/.local/bin/canal-visao quando precisa.

import CoreImage
import Foundation
import ImageIO
import Vision

func carregar(_ caminho: String) -> CGImage? {
    let url = URL(fileURLWithPath: caminho)
    guard let fonte = CGImageSourceCreateWithURL(url as CFURL, nil) else { return nil }
    return CGImageSourceCreateImageAtIndex(fonte, 0, nil)
}

func falhar(_ mensagem: String) -> Never {
    FileHandle.standardError.write((mensagem + "\n").data(using: .utf8)!)
    exit(1)
}

func rostos(_ caminhos: [String]) {
    var saida: [[String: Any]] = []
    for caminho in caminhos {
        guard let imagem = carregar(caminho) else {
            saida.append(["arquivo": caminho, "erro": "não abriu"])
            continue
        }
        let pedido = VNDetectFaceRectanglesRequest()
        let handler = VNImageRequestHandler(cgImage: imagem, options: [:])
        try? handler.perform([pedido])
        let lista: [[String: Double]] = (pedido.results ?? []).map { r in
            let b = r.boundingBox
            return ["x": b.minX, "y": 1 - b.maxY, "w": b.width, "h": b.height, "confianca": Double(r.confidence)]
        }
        saida.append(["arquivo": caminho, "largura": imagem.width, "altura": imagem.height, "rostos": lista])
    }
    let dados = try! JSONSerialization.data(withJSONObject: saida, options: [.prettyPrinted, .sortedKeys])
    print(String(data: dados, encoding: .utf8)!)
}

func recorte(_ entrada: String, _ destino: String) {
    guard let imagem = carregar(entrada) else { falhar("não abriu \(entrada)") }
    let pedido = VNGenerateForegroundInstanceMaskRequest()
    let handler = VNImageRequestHandler(cgImage: imagem, options: [:])
    do {
        try handler.perform([pedido])
        guard let resultado = pedido.results?.first else { falhar("não achei pessoa nem objeto em \(entrada)") }
        let buffer = try resultado.generateMaskedImage(
            ofInstances: resultado.allInstances, from: handler, croppedToInstancesExtent: true)
        let ci = CIImage(cvPixelBuffer: buffer)
        try CIContext().writePNGRepresentation(
            of: ci, to: URL(fileURLWithPath: destino), format: .RGBA8,
            colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)
        print(destino)
    } catch {
        falhar("recorte falhou: \(error.localizedDescription)")
    }
}

let args = Array(CommandLine.arguments.dropFirst())
switch args.first {
case "rostos" where args.count >= 2:
    rostos(Array(args.dropFirst()))
case "recorte" where args.count == 3:
    recorte(args[1], args[2])
default:
    falhar("uso: canal-visao rostos <img>... | canal-visao recorte <entrada> <saida.png>")
}
