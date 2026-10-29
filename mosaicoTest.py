import moderngl
from PIL import Image
import numpy as np

def cargar_textura(ctx, ruta_imagen):
    img = Image.open(ruta_imagen).convert('RGBA')
    texture = ctx.texture(img.size, 4, img.tobytes())
    texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
    return texture

ctx = moderngl.create_standalone_context()

media_tex = cargar_textura(ctx, "reference.jpg")
palette_tex = cargar_textura(ctx, "uPalette.png") # Tira de 60 imágenes

# Configuración del mosaico
COUNT_ELEMENTS = 60.0   # 60 imágenes en uPalette.png
CELLS = 90.0            # Resolución del mosaico

vertex_shader = '''
#version 300 es
precision mediump float;

in vec2 in_position;
in vec2 in_texcoord;

out vec2 vTexCoord;

void main() {
    vTexCoord = in_texcoord;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
'''

fragment_shader = '''
#version 300 es
precision mediump float;

uniform sampler2D uMedia;
uniform sampler2D uPalette;
uniform float uCount;
uniform bool uOriginal;
uniform float uCells;
uniform bool uKeys;

in vec2 vTexCoord;
out vec4 outColor;

vec3 hsl2rgb(vec3 hsl) {
    vec3 rgb = clamp(abs(mod(hsl.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    return hsl.z + hsl.y * (rgb - 0.5) * (1.0 - abs(2.0 * hsl.z - 1.0));
}

float hue(vec4 key) {
    float minC = min(min(key.r, key.g), key.b);
    float maxC = max(max(key.r, key.g), key.b);
    float deltaC = maxC - minC;
    
    float luma = 0.299 * key.r + 0.587 * key.g + 0.114 * key.b;

    float lightness = (maxC + minC) / 2.0;
    float saturation = (lightness == 0.0 || lightness == 1.0) 
                        ? 0.0 
                        : deltaC / (1.0 - abs(2.0 * lightness - 1.0));

    float edgeShare = 0.15; 
    float colorShare = 1.0 - (edgeShare * 2.0);

    if (luma < 0.12 || (saturation < 0.12 && luma < 0.5)) {
        return clamp((luma / 0.5) * edgeShare, 0.0, edgeShare);
    }

    if (luma > 0.88 || (saturation < 0.12 && luma >= 0.5)) {
        float normLuma = (luma - 0.5) / 0.5;
        return clamp((1.0 - edgeShare) + (normLuma * edgeShare), 1.0 - edgeShare, 0.999);
    }

    float huePalette = 0.0;

    if (maxC == key.r) {
        huePalette = mod((key.g - key.b) / deltaC, 6.0);
    } else if (maxC == key.g) {
        huePalette = 2.0 + ((key.b - key.r) / deltaC);
    } else {
        huePalette = 4.0 + ((key.r - key.g) / deltaC);
    }

    huePalette = huePalette / 6.0;
    if (huePalette < 0.0) {
        huePalette += 1.0;
    }

    return clamp(edgeShare + (huePalette * colorShare), edgeShare, 1.0 - edgeShare - 0.001);
}

void main() {
    if (uOriginal) {
        outColor = texture(uMedia, vTexCoord);
        return;
    }

    vec2 symbolCoord = vTexCoord * uCells;
    vec2 stepCoord = floor(symbolCoord);
    
    symbolCoord = fract(symbolCoord); 

    vec2 centerCoord = (stepCoord + vec2(0.5)) / vec2(uCells);
    vec4 key = texture(uMedia, centerCoord);

    if (uKeys) {
        float maxC = max(max(key.r, key.g), key.b);
        float minC = min(min(key.r, key.g), key.b);
        float deltaC = maxC - minC;

        float hueColor = hue(key);
        float lightnessColor = (maxC + minC) / 2.0;
        float saturationColor = (lightnessColor == 0.0 || lightnessColor == 1.0) ? 0.0 : deltaC / (1.0 - abs(2.0 * lightnessColor - 1.0));

        outColor = vec4(hsl2rgb(vec3(hueColor, saturationColor, lightnessColor)), 1.0);
        return;
    }

    float hueColor = hue(key);
    float imgIndex = clamp(floor(hueColor * uCount), 0.0, uCount - 1.0);

    float padding = 0.5 / (uCount * 64.0);
    float localS = mix(padding, 1.0 - padding, symbolCoord.s);

    vec2 paletteCoord = vec2(
        (imgIndex + localS) / uCount,
        symbolCoord.t
    );

    outColor = texture(uPalette, paletteCoord);
}
'''

prog = ctx.program(
    vertex_shader=vertex_shader,
    fragment_shader=fragment_shader
)

# Configurar Uniforms
prog['uMedia'].value = 0
prog['uPalette'].value = 1
prog['uCount'].value = COUNT_ELEMENTS
prog['uCells'].value = CELLS
prog['uOriginal'].value = False

# IMPORTANTE: Desactivar uKeys para proyectar las imágenes de uPalette.png
prog['uKeys'].value = False

vertices = np.array([
    -1.0, -1.0, 0.0, 0.0,
     1.0, -1.0, 1.0, 0.0,
    -1.0,  1.0, 0.0, 1.0,
     1.0,  1.0, 1.0, 1.0,
], dtype='f4')

vbo = ctx.buffer(vertices.tobytes())
vao = ctx.simple_vertex_array(prog, vbo, 'in_position', 'in_texcoord')

width, height = media_tex.size
fbo = ctx.framebuffer(color_attachments=[ctx.texture((width, height), 4)])
fbo.use()

media_tex.use(location=0)
palette_tex.use(location=1)

vao.render(moderngl.TRIANGLE_STRIP)

data = fbo.read(components=4)
resultado = Image.frombytes('RGBA', (width, height), data)
resultado.save("mosaico_resultado.png")

print("¡Mosaico procesado respetando el shader intacto!")