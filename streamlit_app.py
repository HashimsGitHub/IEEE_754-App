import streamlit as st
import struct
from decimal import Decimal, getcontext, InvalidOperation

# ================= Helper Functions =================

def float_to_ieee_bits(value: float) -> tuple[str, str]:
    packed = struct.pack('>f', value)
    as_int = int.from_bytes(packed, 'big')
    bits = f"{as_int:032b}"
    hx = f"0x{as_int:08X}"
    return bits, hx

def ieee_bits_to_float(bits: str) -> float:
    as_int = int(bits, 2)
    packed = as_int.to_bytes(4, 'big')
    return struct.unpack('>f', packed)[0]

def bits_to_components(bits: str) -> dict[str, object]:
    s = bits[0]
    e = bits[1:9]
    m = bits[9:]
    bias = 127
    exp_val = int(e, 2)
    unbiased = exp_val - bias
    return {
        'sign_bit': s,
        'exponent_bits': e,
        'mantissa_bits': m,
        'exponent_biased': exp_val,
        'exponent_unbiased': unbiased,
        'bias': bias
    }

def create_bitfield_html(bits: str) -> str:
    """Color-coded bitfield: Sign (red), Exponent (yellow), Mantissa (green)"""
    sign_color = '#f28b82'
    exp_color = '#fbbc04'
    mant_color = '#34a853'

    s = bits[0]
    e = bits[1:9]
    m = bits[9:]

    style = f"""
    <style>
    .bitfield {{ font-family: monospace; display: flex; flex-wrap: wrap; justify-content: center; margin: 10px 0; }}
    .bit {{ padding: 4px; margin: 1px; border-radius: 4px; color: white; font-size: 14px; text-align: center; }}
    .sign {{ background-color: {sign_color}; }}
    .exp {{ background-color: {exp_color}; }}
    .mant {{ background-color: {mant_color}; }}
    </style>
    """

    html = style + '<div class="bitfield">'
    html += f'<div class="bit sign">{s}</div>'
    html += ''.join([f'<div class="bit exp">{b}</div>' for b in e])
    html += ''.join([f'<div class="bit mant">{b}</div>' for b in m])
    html += '</div>'
    html += f'<p><b>Legend:</b> <span style="color:{sign_color}">Sign</span>, <span style="color:{exp_color}">Exponent</span>, <span style="color:{mant_color}">Mantissa</span></p>'

    return html

def create_final_boxes_html(bits: str, hx: str) -> str:
    """Show final 32-bit number in 8 boxes + HEX box"""
    bit_groups = [bits[i:i+4] for i in range(0, 32, 4)]
    
    style = """
    <style>
    .final-field { display: flex; justify-content: center; flex-wrap: wrap; margin: 10px 0; }
    .bit-box { padding: 10px; margin: 3px; border-radius: 4px; font-family: monospace; font-size: 16px; text-align: center; border: 1px solid #555; background-color: #1976D2; color: white; font-weight: bold; }
    .hex-box { padding: 10px; margin: 3px; border-radius: 4px; font-family: monospace; font-size: 16px; text-align: center; border: 1px solid #555; background-color: #4CAF50; color: white; font-weight: bold; }
    </style>
    """
    html = style + '<div class="final-field">'
    for grp in bit_groups:
        html += f'<div class="bit-box">{grp}</div>'
    html += '</div>'
    # HEX box
    html += f'<div class="final-field"><div class="hex-box">{hx}</div></div>'
    return html

def parse_binary_fraction(value: str) -> float:
    value = value.strip()
    if not value:
        raise ValueError("Binary input cannot be empty.")

    sign = 1
    if value.startswith('+'):
        value = value[1:]
    elif value.startswith('-'):
        sign = -1
        value = value[1:]

    if '.' in value:
        int_part_str, frac_part_str = value.split('.')
    else:
        int_part_str, frac_part_str = value, ''

    if not all(c in '01' for c in int_part_str + frac_part_str):
        raise ValueError("Binary input must contain only 0 and 1 digits, optionally a single dot.")

    int_value = int(int_part_str, 2) if int_part_str else 0
    frac_value = sum(int(b)*(2**-(i+1)) for i, b in enumerate(frac_part_str))
    return sign * (int_value + frac_value)

def decimal_to_ieee_steps(value_str: str) -> tuple[str, str, str]:
    try:
        getcontext().prec = 80
        dec = Decimal(value_str)
    except InvalidOperation:
        raise ValueError("Invalid decimal input. Please enter a valid number.")

    sign = 0
    if dec < 0:
        sign = 1
        dec = -dec

    int_part = int(dec // 1)
    frac_part = dec - int_part

    int_bin = bin(int_part)[2:] if int_part != 0 else '0'

    frac_bits = ''
    frac = frac_part
    for _ in range(40):
        frac *= 2
        bit = '1' if frac >= 1 else '0'
        if frac >= 1:
            frac -= 1
        frac_bits += bit
        if frac == 0:
            break

    if int_part != 0:
        exponent_unbiased = len(int_bin) - 1
        mantissa_raw = int_bin[1:] + frac_bits
    else:
        first_one = frac_bits.find('1')
        if first_one == -1:
            raise ValueError("Invalid input: cannot normalize 0.0.")
        exponent_unbiased = -(first_one + 1)
        mantissa_raw = frac_bits[first_one + 1:]

    bias = 127
    exponent_biased = exponent_unbiased + bias

    if not (0 <= exponent_biased <= 255):
        raise ValueError("Value out of range for IEEE-754 single precision.")

    exponent_bits = f"{exponent_biased:08b}"
    mantissa = mantissa_raw[:23].ljust(23, '0')

    bits = f"{sign:b}" + exponent_bits + mantissa
    hx = f"0x{int(bits, 2):08X}"

    html = f"""
    <h3>Conversion Steps for {value_str}</h3>
    <p>Sign bit: {sign}</p>
    <p>Integer part: {int_part} (binary {int_bin})</p>
    <p>Fractional part: {frac_part} → binary {frac_bits}</p>
    <p>Exponent (unbiased): {exponent_unbiased}, Biased: {exponent_biased}</p>
    <p>Exponent bits: {exponent_bits}</p>
    <p>Mantissa bits: {mantissa}</p>
    <p>Final IEEE bits:</p>
    """
    return bits, hx, html

def parse_hex_input(value: str) -> tuple[str, str, str]:
    v = value.strip().lower()
    if v.startswith('0x'):
        v = v[2:]
    if len(v) != 8 or not all(c in '0123456789abcdef' for c in v):
        raise ValueError("Invalid HEX input. Please enter 8 hexadecimal digits (optionally prefixed with 0x).")

    as_int = int(v, 16)
    bits = f"{as_int:032b}"
    hx = f"0x{as_int:08X}"  # <-- Ensure HEX is defined
    float_val = ieee_bits_to_float(bits)

    comps = bits_to_components(bits)
    html = f"""
    <h3>Interpretation of 0x{v.upper()}</h3>
    <p>Sign bit: {comps['sign_bit']}</p>
    <p>Exponent bits: {comps['exponent_bits']} (biased {comps['exponent_biased']}, unbiased {comps['exponent_unbiased']})</p>
    <p>Mantissa bits: {comps['mantissa_bits']}</p>
    """
    return bits, float_val, html

# ================= Streamlit App =================

st.set_page_config(page_title='IEEE-754 Converter', layout='wide')
st.title("🎈 Hashim's IEEE-754 Converter — 32-bit Floating Point")

with st.sidebar:
    st.header('Input Type')
    input_type = st.radio('Choose Input Type', ['Decimal', 'Hexadecimal', 'Binary'])

st.markdown('Enter a value below to view its IEEE-754 32-bit conversion steps and bitfield visualization.')
input_str = st.text_input('Input value', value='3.1415926')

if st.button('Convert'):
    try:
        if input_type == 'Decimal':
            bits, hx, html = decimal_to_ieee_steps(input_str)
        elif input_type == 'Hexadecimal':
            bits, _, html = parse_hex_input(input_str)
            hx = f"0x{int(bits, 2):08X}"  # <-- Ensure hx is defined
        else:  # Binary input
            dec_value = parse_binary_fraction(input_str)
            bits, hx, html = decimal_to_ieee_steps(str(dec_value))
            st.markdown(f"<p>Parsed Decimal value from binary input: {dec_value}</p>", unsafe_allow_html=True)

        st.markdown(html, unsafe_allow_html=True)
        st.markdown(create_bitfield_html(bits), unsafe_allow_html=True)
        st.markdown(create_final_boxes_html(bits, hx), unsafe_allow_html=True)

    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Unexpected error: {e}")

st.markdown('---')
st.caption('This app converts Decimal, Hexadecimal, or Binary (fixed-point) input into IEEE-754 32-bit floating point format with color-coded bitfield and final binary/HEX display.')
