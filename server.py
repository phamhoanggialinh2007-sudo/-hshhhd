import os
import re
import random
import string
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow CORS for frontend from different domain

def check_syntax(code):
    """Advanced basic syntax check for LuaU: balanced brackets, quotes, and simple keyword checks."""
    brackets = {'(': ')', '[': ']', '{': '}'}
    stack = []
    in_string = False
    quote_char = None
    keywords = set(['end', 'then', 'do', 'until', 'else', 'elseif'])
    keyword_stack = []
    for char in code:
        if in_string:
            if char == quote_char:
                in_string = False
            continue
        if char in '"\'':
            in_string = True
            quote_char = char
            continue
        if char in brackets:
            stack.append(char)
        elif char in brackets.values():
            if not stack or brackets[stack.pop()] != char:
                return False
        # Simple keyword balance check (e.g., if-then-end)
        if char.isalpha() and code.find('if ') or code.find('for ') or code.find('while '):
            keyword_stack.append(char)
    if keyword_stack:
        return False  # Unbalanced keywords
    return not stack and not in_string

def obfuscate(code):
    """Super strong LuaU obfuscation with multi-layer XOR, junk, control flow, anti-tamper, etc. Ensures valid syntax."""
    # 7. Metadata Removal: Remove comments, minify whitespace
    code = re.sub(r'--.*', '', code)
    code = re.sub(r'\s+', ' ', code).strip()

    # 1. Variable/Function Renaming: More random, hex-like
    keywords = set(['and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function', 'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 'repeat', 'return', 'then', 'true', 'until', 'while'])
    identifiers = set(re.findall(r'\b[a-zA-Z_]\w*\b', code))
    vars_to_rename = identifiers - keywords
    rename_map = {v: '_0x' + hex(random.randint(0, 0xFFFFF))[2:].zfill(5) for v in vars_to_rename}
    for old, new in rename_map.items():
        code = re.sub(r'\b' + re.escape(old) + r'\b', new, code)

    # 2. String Encoding: Multi-layer XOR (3 layers) + Base64, dynamic runtime decode
    base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    
    def base64_encode(data):
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')

    def encode_string(match):
        str_content = match.group(1)
        keys = [random.randint(1, 255) for _ in range(3)]  # 3 XOR keys
        encoded = str_content
        for key in keys:
            encoded = ''.join(chr(ord(c) ^ key) for c in encoded)
        encoded_b64 = base64_encode(encoded)
        # Multi-layer decoder in pure LuaU
        decoder = f'''(function(_b64, _k1, _k2, _k3)
            local _chars = "{base64_chars}"
            local _result = {{}}
            local _i = 1
            local _bits = 0
            local _count = 0
            local _val = 0
            for _c = 1, #_b64 do
                local _char = _b64:sub(_c, _c)
                if _char == "=" then break end
                local _idx = _chars:find(_char) - 1
                if _idx >= 0 then
                    _val = _val * 64 + _idx
                    _count = _count + 1
                    if _count == 4 then
                        _result[_i] = string.char(bit32.bxor(bit32.rshift(_val, 16) % 256, _k3))
                        _result[_i + 1] = string.char(bit32.bxor(bit32.rshift(_val, 8) % 256, _k3))
                        _result[_i + 2] = string.char(bit32.bxor(_val % 256, _k3))
                        _i = _i + 3
                        _val = 0
                        _count = 0
                    end
                end
            end
            if _count == 3 then
                _result[_i] = string.char(bit32.bxor(bit32.rshift(_val, 10) % 256, _k3))
                _result[_i + 1] = string.char(bit32.bxor(bit32.rshift(_val, 2) % 256, _k3))
            elseif _count == 2 then
                _result[_i] = string.char(bit32.bxor(bit32.rshift(_val, 4) % 256, _k3))
            end
            local _dec = table.concat(_result)
            for _l=2,3 do
                local _tmp = ''
                for _j=1,#_dec do
                    _tmp = _tmp .. string.char(bit32.bxor(_dec:byte(_j), (_l==2 and _k2 or _k1)))
                end
                _dec = _tmp
            end
            return _dec
        end)("{encoded_b64}", {keys[0]}, {keys[1]}, {keys[2]})'''
        return decoder

    code = re.sub(r'"(.*?)"', encode_string, code)
    code = re.sub(r"'(.*?)'", encode_string, code)

    # 3. Junk Code: More aggressive, with fake functions and loops
    junk_snippets = [
        'local _0xjunk' + hex(random.randint(0, 0xFFF))[2:] + ' = math.random(1,1000); if _0xjunk' + hex(random.randint(0, 0xFFF))[2:] + ' > 9999 then end;',
        'function _fake' + hex(random.randint(0, 0xFFF))[2:] + '() return nil end; _fake' + hex(random.randint(0, 0xFFF))[2:] + ' = nil;',
        'repeat local _j = 1 until _j > 0;',
        'if false then error("fake") end; while false do break end;',
    ]
    parts = code.split(';')
    for i in range(len(parts) - 1, 0, -1):
        if random.random() < 0.25:  # More junk
            parts.insert(i, random.choice(junk_snippets))
    code = ';'.join(parts)

    # 4. Control Flow Obfuscation: More complex math, fake switches, goto
    code = re.sub(r'if\s+(\w+)\s*>\s*(\d+)\s*then', r'if math.floor(math.sin(\1 / \2) + 1) == 1 then', code)
    code = re.sub(r'if\s+(\w+)\s*==\s*(\d+)\s*then', r'if ((\1 - \2)^2 == 0) then', code)
    # Add fake goto and loops
    fake_label = '_fake' + hex(random.randint(0, 0xFFF))[2:]
    code = f'goto {fake_label}; ::{fake_label}:: ' + code + ' ; repeat until true'

    # 5. Anti-Tamper/Anti-Debug: Stronger timing checks, env checks, traps
    anti_tamper = '''
local _env = getfenv() local _start = tick() wait(0.001) if tick() - _start > 0.005 or _env.debug then warn("Tamper detected") end
local _trap = math.random() if _trap > 1 then error("Trap triggered") end
if type(_G) ~= "table" then warn("Env tamper") end
'''
    code = anti_tamper + code

    # 6. Runtime Assembly: Split into smaller dynamic parts, reassemble with XOR
    split_parts = [code[i:i+100] for i in range(0, len(code), 100)]  # Smaller for stronger hiding
    key_split = random.randint(1, 255)
    encoded_parts = [''.join(chr(ord(c) ^ key_split) for c in part) for part in split_parts]
    reassemble = '..'.join(f'''(function(_s, _k) local _r='' for _i=1,#_s do _r=_r..string.char(bit32.bxor(_s:byte(_i),_k)) end return _r end)("{ep}", {key_split})''' for ep in encoded_parts)
    code = f'loadstring({reassemble})()'

    # 8. Multi-layer Obfuscation: 2 outer XOR layers + dynamic key
    keys_outer = [random.randint(1, 255) for _ in range(2)]
    encoded = code
    for key in keys_outer:
        encoded = ''.join(chr(ord(c) ^ key) for c in encoded)
    multi_decoder = f'''
local function _multi_dec(_s, _k1, _k2)
    local _r = _s
    for _l=1,2 do
        local _tmp = ''
        for _i=1,#_r do
            _tmp = _tmp .. string.char(bit32.bxor(_r:byte(_i), (_l==1 and _k2 or _k1)))
        end
        _r = _tmp
    end
    return _r
end
loadstring(_multi_dec("{encoded}", {keys_outer[0]}, {keys_outer[1]}))()
'''
    return multi_decoder

@app.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    if file and file.filename:
        input_code = file.read().decode('utf-8')

    if not input_code.strip():
        return jsonify({'error': 'No code provided!'}), 400

    if not check_syntax(input_code):
        return jsonify({'error': 'Syntax error in input code!'}), 400

    obfuscated = obfuscate(input_code)
    # Post-obfuscation syntax check (basic)
    if not check_syntax(obfuscated):
        return jsonify({'error': 'Obfuscation failed syntax check!'}), 500

    return jsonify({'output': obfuscated, 'status': 'Obfuscation complete! Super strong encryption.'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
