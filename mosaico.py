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
palette_tex = cargar_textura(ctx, "uPalette.png")

# Configuración del mosaico
COUNT_ELEMENTS = 30.0   
CELLS = 90.0           

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

float hue(vec4 key) {
    float minC = min(min(key.r, key.g), key.b);
    float maxC = max(max(key.r, key.g), key.b);
    float deltaC = maxC - minC;

    float huePalette = 0.0;

    if (deltaC != 0.0) {
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
    }

    return clamp(huePalette, 0.0, 0.999);
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
        outColor = key;
        return;
    }

    float hueColor = hue(key);
    float imgIndex = clamp(floor(hueColor * uCount), 0.0, uCount - 1.0);

    // Margen subpíxel para evitar sangrado de bordes entre mosaicos
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
resultado = resultado.transpose(Image.FLIP_TOP_BOTTOM) 
resultado.save("mosaico_resultado.png")

print("¡Mosaico procesado con éxito!")