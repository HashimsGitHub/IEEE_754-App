import streamlit as st

st.title("🎈 Hashim's IEEE-754 App")
st.write(
    "This app shows IEEE-754 floating-point conversion with step-by-step logic and color-coded bitfield visualization"
)

import streamlit as st
import struct
from decimal import Decimal, getcontext

# ================= Helper Functions =================

def float_to_ieee_bits(value: float) -> (str, str):
    packed = struct.pack('>f', value)
    as_int = int.from_bytes(packed, 'big')
    bits = f"{as_int:032b}"
    hx = f"0x{as_int:08X}"
    return bits, hx


def bits_to_components(bits: str) -> dict:
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

    legend = f'<p><b>Legend:</b> <span style="color:{sign_color}">Sign</span>, <span style="color:{exp_color}">Exponent</span>, <span style="color:{mant_color}">Mantissa</span></p>'
    return html + legend


def decimal_to_binary_fraction(decimal_fraction: Decimal, limit_bits: int) -> (str, list):
    steps = []
    bits = ''
    frac = decimal_fraction
    for i in range(limit_bits):
        frac *= 2
        bit = '1' if frac >= 1 else '0'
        if bit == '1':
            frac -= 1
        bits += bit
        steps.append(f"Step {i+1}: multiply by 2 → bit={bit}, remaining fraction={frac}")
        if frac == 0:
            break
    return bits, steps


def decimal_to_ieee_steps(value_str: str) -> (str, str, str):
    getcontext().prec = 80
    dec = Decimal(value_str)

    sign = 0
    if dec < 0:
        sign = 1
        dec = -dec

    int_part = int(dec // 1)
    frac_part = dec - int_part

    int_bin = bin(int_part)[2:] if int_part != 0 else '0'
    mantissa_bits_count = 23
    frac_bits_limit = mantissa_bits_count + 10
    frac_bits, frac_steps = decimal_to_binary_fraction(frac_part, frac_bits_limit)

    if int_part != 0:
        exponent_unbiased = len(int_bin) - 1
        mantissa_raw = int_bin[1:] + frac_bits
    else:
        first_one = frac_bits.find('1')
        exponent_unbiased = -(first_one + 1)
        mantissa_raw = frac_bits[first_one+1:]

    bias = 127
    exponent_biased = exponent_unbiased + bias
    exponent_bits = f"{exponent_biased:08b}"
    mantissa = mantissa_raw[:mantissa_bits_count].ljust(mantissa_bits_count, '0')

    bits = f"{sign:b}" + exponent_bits + mantissa
    hx = f"0x{int(bits,2):08X}"

    html = [
        f"<h3>Conversion Steps for {value_str}</h3>",
        f"<p>Sign bit: {sign}</p>",
        f"<p>Integer part: {int_part} (binary {int_bin})</p>",
        f"<p>Fractional part: {frac_part} → binary {frac_bits}</p>",
        "<ol>" + ''.join([f"<li>{s}</li>" for s in frac_steps]) + "</ol>",
        f"<p>Exponent (unbiased): {exponent_unbiased}, Biased: {exponent_biased}</p>",
        f"<p>Exponent bits: {exponent_bits}</p>",
        f"<p>Mantissa bits: {mantissa}</p>",
        f"<p>Final IEEE bits: {bits}</p>",
        f"<p>Hex representation: {hx}</p>"
    ]
    return bits, hx, '\n'.join(html)


def parse_hex_input(value: str) -> (str, str, str):
    v = value.strip().lower()
    if v.startswith('0x'):
        v = v[2:]
    if len(v) != 8:
        raise ValueError("Hex input must be exactly 8 hex digits (32 bits).")
    as_int = int(v, 16)
    bits = f"{as_int:032b}"
    comps = bits_to_components(bits)

    html = [
        f"<h3>Interpretation of 0x{v.upper()}</h3>",
        f"<p>Sign bit: {comps['sign_bit']}</p>",
        f"<p>Exponent bits: {comps['exponent_bits']} (biased {comps['exponent_biased']}, unbiased {comps['exponent_unbiased']})</p>",
        f"<p>Mantissa bits: {comps['mantissa_bits']}</p>"
    ]
    return bits, '0x'+v.upper(), '\n'.join(html)

# ================= Streamlit App =================

st.set_page_config(page_title='IEEE-754 Converter', layout='wide')
st.title('IEEE-754 Converter — 32-bit Floating Point with Visual Bitfields')

with st.sidebar:
    st.header('Input Type')
    input_type = st.radio('Choose Input Type', ['Decimal', 'Hexadecimal'])

st.markdown('Enter a value below to view its IEEE-754 32-bit conversion steps and bitfield visualization.')
input_str = st.text_input('Input value', value='3.1415926')

if st.button('Convert'):
    try:
        if input_type == 'Decimal':
            bits, hx, html = decimal_to_ieee_steps(input_str)
        else:
            bits, hx, html = parse_hex_input(input_str)

        st.markdown(html, unsafe_allow_html=True)
        st.subheader('Bitfield Visualization')
        st.markdown(create_bitfield_html(bits), unsafe_allow_html=True)

        st.text_area('IEEE Bits', bits, height=80)
        st.text_input('Hexadecimal Representation', hx)

        comps = bits_to_components(bits)
        st.markdown(f"**Sign bit:** {comps['sign_bit']}")
        st.markdown(f"**Exponent bits:** {comps['exponent_bits']} (biased: {comps['exponent_biased']}, unbiased: {comps['exponent_unbiased']})")
        st.markdown(f"**Mantissa bits:** {comps['mantissa_bits']}")

    except Exception as e:
        st.error(f"Error: {e}")

st.markdown('---')
st.caption('This app converts Decimal or Hexadecimal input into IEEE-754 32-bit format and visualizes the bitfields.')
