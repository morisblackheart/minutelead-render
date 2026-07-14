#!/usr/bin/env python3
"""MinuteLead featured images — each post is its OWN bespoke flat illustration.
NO shared phone/agent motif. Brand cohesion = warm-paper bg, navy/orange/green/coral flat
style, recurring green 'booked' check + orange spark cues placed differently per post.
Text-free, no logo. Safe zone x in [110,1090] (Elementor grid center-crops ~1.5:1)."""
import subprocess, os, json
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,"out")
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
NV="#15233B"; OR="#F2960F"; GR="#2FBF71"; CO="#E0664F"; BL="#EAF0F6"; CR="#FBF8F2"

# ---------- reusable brand components (absolute coords unless wrapped) ----------
def ground(cx,rx,cy=566):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="30" fill="#EBE3D4" opacity=".7"/>'
def badge_check(cx,cy,r=24):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{GR}"/><path d="M{cx-r*0.42} {cy} l{r*0.33} {r*0.34} l{r*0.6} -{r*0.66}" stroke="#fff" stroke-width="{r*0.17}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
def card_booked(x,y):
    return (f'<rect x="{x}" y="{y}" width="158" height="110" rx="16" fill="#fff" stroke="#EFE6D7"/>'
            f'<rect x="{x}" y="{y}" width="158" height="30" rx="16" fill="{NV}"/><rect x="{x}" y="{y+15}" width="158" height="15" fill="{NV}"/>'
            f'<circle cx="{x+24}" cy="{y+15}" r="4" fill="{OR}"/><circle cx="{x+134}" cy="{y+15}" r="4" fill="{OR}"/>'
            + ''.join(f'<rect x="{x+18+ (i%4)*32}" y="{y+44+(i//4)*26}" width="22" height="18" rx="3" fill="{BL}"/>' for i in range(7))
            + f'<rect x="{x+50}" y="{y+70}" width="22" height="18" rx="3" fill="{GR}"/>'
            + badge_check(x+138,y+92,17))
def moon(cx,cy,r=70):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FBF3E2"/><circle cx="{cx+r*0.42}" cy="{cy-r*0.34}" r="{r*0.86}" fill="{CR}"/>'
def stars(pts):
    return '<g fill="#F2C06A">'+''.join(f'<circle cx="{x}" cy="{y}" r="{s}"/>' for x,y,s in pts)+'</g>'
def sun(cx,cy,r=58):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#F7E2BC"/><circle cx="{cx}" cy="{cy}" r="{r*0.7}" fill="#FBEFD2"/>'
def clock(cx,cy,r=46):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" stroke="{NV}" stroke-width="5"/>'
            f'<path d="M{cx} {cy} V{cy-r*0.6}M{cx} {cy} L{cx+r*0.4} {cy+r*0.18}" stroke="{NV}" stroke-width="5" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="5" fill="{OR}"/>')
def headset(cx,cy):
    return (f'<g transform="translate({cx},{cy})" fill="none" stroke="{NV}" stroke-width="5" stroke-linecap="round">'
            f'<path d="M-16 6v-3a16 16 0 0 1 32 0v3"/><path d="M-16 6h8v12h-6a2 2 0 0 1-2-2zM16 6h-8v12h6a2 2 0 0 0 2-2z" fill="{NV}"/></g>')
def sms(x,y):
    return (f'<rect x="{x}" y="{y}" width="124" height="58" rx="16" fill="{NV}"/><path d="M{x+22} {y+58} l-6 18 22 -12 z" fill="{NV}"/>'
            f'<circle cx="{x+34}" cy="{y+29}" r="5" fill="#9FB0C4"/><circle cx="{x+58}" cy="{y+29}" r="5" fill="#9FB0C4"/><circle cx="{x+82}" cy="{y+29}" r="5" fill="{OR}"/>')
def missed_tag(x,y):
    return (f'<rect x="{x}" y="{y}" width="150" height="56" rx="16" fill="#FBF1EE" stroke="#F1D8D0"/>'
            f'<g transform="rotate(135 {x+30} {y+28})"><circle cx="{x+30}" cy="{y+28}" r="15" fill="{CO}"/>'
            f'<path d="M{x+22} {y+24}c1 5 6 9 11 9 2 0 3-2 3-4l-1-4c0-1-3-2-4-1l-2 0c-2-1-4-3-5-5l0-2c1-1 0-3-1-4l-4-1c-2 0-3 1-3 3z" fill="#fff"/></g>'
            f'<rect x="{x+56}" y="{y+19}" width="74" height="7" rx="3.5" fill="#C24B36"/><rect x="{x+56}" y="{y+33}" width="48" height="7" rx="3.5" fill="#E7B6AA"/>')
def estimate_doc(x,y):
    return (f'<rect x="{x}" y="{y}" width="128" height="160" rx="12" fill="#fff" stroke="{NV}" stroke-width="3"/>'
            f'<circle cx="{x+34}" cy="{y+38}" r="18" fill="{OR}"/><path d="M{x+34} {y+28}v20M{x+29} {y+33}h8a3 3 0 0 1 0 6h-6a3 3 0 0 0 0 6h8" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
            f'<rect x="{x+62}" y="{y+30}" width="50" height="7" rx="3.5" fill="{NV}"/><rect x="{x+62}" y="{y+44}" width="38" height="7" rx="3.5" fill="#C9C3B6"/>'
            f'<g fill="#E6E0D4"><rect x="{x+18}" y="{y+74}" width="92" height="7" rx="3.5"/><rect x="{x+18}" y="{y+92}" width="92" height="7" rx="3.5"/><rect x="{x+18}" y="{y+110}" width="64" height="7" rx="3.5"/></g>')
def spark(x1,y1,x2,y2):
    return f'<path d="M{x1} {y1} C{(x1+x2)//2} {y1}, {(x1+x2)//2} {y2}, {x2} {y2}" stroke="{OR}" stroke-width="3" fill="none" stroke-dasharray="2 7" stroke-linecap="round"/>'

# ---------- per-trade hero subjects ----------
def hub_funnel(cx,cy,dirn=1):
    sx=cx-dirn*210; cardx=cx+96 if dirn==1 else cx-96-158
    dots=''.join(f'<circle cx="{sx}" cy="{cy+dy}" r="9" fill="{c}"/><line x1="{sx}" y1="{cy+dy}" x2="{cx-dirn*26}" y2="{cy}" stroke="{NV}" stroke-opacity=".26" stroke-width="1.6"/>'
                 for dy,c in [(-72,CO),(-2,OR),(70,NV)])
    return (dots
        +f'<circle cx="{cx}" cy="{cy}" r="52" fill="url(#glow)"/><circle cx="{cx}" cy="{cy}" r="30" fill="{OR}"/><circle cx="{cx}" cy="{cy}" r="18" fill="{NV}"/><circle cx="{cx}" cy="{cy}" r="6.5" fill="{OR}"/>'
        +f'<line x1="{cx+dirn*30}" y1="{cy}" x2="{cx+dirn*96}" y2="{cy-44}" stroke="{OR}" stroke-width="2.4"/><line x1="{cx+dirn*30}" y1="{cy}" x2="{cx+dirn*96}" y2="{cy+44}" stroke="{OR}" stroke-width="2.4"/>'
        +card_booked(cardx,cy-100)+card_booked(cardx,cy+12))
def H_lock(x,y):
    # paneled door (navy frame, recessed panels) + knob + deadbolt on the latch side; standalone key beside
    return (f'<g transform="translate({x},{y})"><rect x="0" y="0" width="150" height="278" rx="8" fill="{NV}"/>'
            f'<rect x="12" y="12" width="126" height="254" rx="4" fill="{BL}"/>'
            f'<rect x="28" y="30" width="94" height="96" rx="4" fill="none" stroke="{NV}" stroke-width="4"/>'
            f'<rect x="28" y="148" width="94" height="96" rx="4" fill="none" stroke="{NV}" stroke-width="4"/>'
            f'<circle cx="120" cy="150" r="8" fill="{OR}"/>'
            f'<circle cx="120" cy="116" r="14" fill="{OR}"/><circle cx="120" cy="116" r="14" fill="none" stroke="{NV}" stroke-width="3"/>'
            f'<circle cx="120" cy="112" r="4" fill="{NV}"/><path d="M120 112 l-3 11 h6 z" fill="{NV}"/></g>'
            f'<g transform="translate({x+188},{y+158})"><circle r="24" fill="none" stroke="{OR}" stroke-width="11"/><rect x="18" y="-7" width="74" height="14" rx="5" fill="{OR}"/><rect x="70" y="-3" width="9" height="20" fill="{OR}"/><rect x="86" y="-3" width="9" height="26" fill="{OR}"/></g>')
def H_roof(x,y):
    return (f'<g transform="translate({x},{y})"><rect x="60" y="150" width="210" height="130" rx="8" fill="{BL}"/>'
            f'<rect x="96" y="190" width="50" height="50" rx="6" fill="{CR}" stroke="{NV}" stroke-width="3"/><path d="M121 190v50M96 215h50" stroke="{NV}" stroke-width="3"/>'
            f'<rect x="190" y="190" width="54" height="90" rx="5" fill="{NV}"/><circle cx="232" cy="238" r="4" fill="{OR}"/>'
            f'<path d="M40 156 L165 50 L290 156 Z" fill="{OR}"/><g stroke="#C97A0C" stroke-width="3" opacity=".7"><path d="M72 132h186M92 110h146M112 88h106M132 66h66"/></g>'
            f'<g stroke="{NV}" stroke-width="5" stroke-linecap="round"><path d="M276 120 L330 280M296 120 L350 280"/><path d="M283 144h24M290 174h24M297 204h24M304 234h24"/></g></g>')
def H_electric(x,y):
    sw=''.join(f'<rect x="{36+(i%2)*54}" y="{40+(i//2)*30}" width="40" height="18" rx="4" fill="{OR if i==2 else CR}" stroke="{NV}" stroke-width="2"/>' for i in range(6))
    return (f'<g transform="translate({x},{y})"><rect x="16" y="8" width="148" height="200" rx="14" fill="{NV}"/><rect x="28" y="24" width="124" height="170" rx="8" fill="{CR}"/>{sw}'
            f'<path d="M92 140 q-30 18 -8 44 q22 22 -2 40" fill="none" stroke="{NV}" stroke-width="4" stroke-linecap="round"/>'
            f'<path d="M214 -28 L150 60 h38 l-14 60 70 -94 h-42 z" fill="{OR}" stroke="{NV}" stroke-width="2" stroke-linejoin="round"/></g>')
def H_hvac(x,y):
    return (f'<g transform="translate({x},{y})"><rect x="20" y="40" width="220" height="180" rx="16" fill="{NV}"/><rect x="36" y="56" width="188" height="148" rx="8" fill="{BL}"/>'
            f'<circle cx="130" cy="130" r="62" fill="{CR}" stroke="{NV}" stroke-width="3"/>'
            f'<g transform="translate(130,130)" fill="none" stroke="{NV}" stroke-width="7" stroke-linecap="round"><path d="M0 -50a50 50 0 0 1 43 25"/><path d="M0 -50a50 50 0 0 0 -43 25"/><path d="M25 41a50 50 0 0 0 18 -43"/></g><circle cx="130" cy="130" r="13" fill="{OR}"/>'
            f'<g stroke="{OR}" stroke-width="6" fill="none" stroke-linecap="round"><path d="M252 80 q30 22 0 44"/><path d="M252 128 q40 28 0 56"/></g></g>')
def H_plumb(x,y):
    return (f'<g transform="translate({x},{y})"><path d="M40 10 v80 a50 50 0 0 0 100 0 v-12" fill="none" stroke="{NV}" stroke-width="18" stroke-linecap="round"/>'
            f'<rect x="22" y="2" width="38" height="26" rx="6" fill="{NV}"/><circle cx="140" cy="86" r="10" fill="{OR}"/>'
            f'<g fill="{GR}"><path d="M96 150c-10-6-15-18-7-27 6 7 7 18 7 27z"/><path d="M96 150c10-6 15-18 7-27-6 7-7 18-7 27z"/></g>'
            f'<g fill="{GR}" opacity=".85"><circle cx="62" cy="210" r="10"/><circle cx="128" cy="232" r="8"/><circle cx="96" cy="256" r="12"/></g>'
            f'<g transform="rotate(40 210 170)"><rect x="192" y="100" width="24" height="130" rx="9" fill="{NV}"/><path d="M192 100 a20 20 0 1 1 24 0 l-9 9 h-6 z" fill="{NV}"/><circle cx="204" cy="113" r="8" fill="{CR}"/></g></g>')
def H_cal(x,y):
    return (f'<g transform="translate({x},{y})"><rect x="0" y="0" width="230" height="200" rx="18" fill="#fff" stroke="{NV}" stroke-width="3"/>'
            f'<rect x="0" y="0" width="230" height="50" rx="18" fill="{NV}"/><rect x="0" y="30" width="230" height="20" fill="{NV}"/>'
            f'<circle cx="38" cy="-2" r="7" fill="{OR}"/><circle cx="192" cy="-2" r="7" fill="{OR}"/><rect x="30" y="-18" width="14" height="26" rx="6" fill="{NV}"/><rect x="186" y="-18" width="14" height="26" rx="6" fill="{NV}"/>'
            +''.join(f'<rect x="{22+(i%4)*52}" y="{72+(i//4)*42}" width="36" height="30" rx="5" fill="{BL}"/>' for i in range(11))
            +f'<rect x="{22+1*52}" y="{72+1*42}" width="36" height="30" rx="5" fill="{GR}"/>'+badge_check(196,176,26)+'</g>')
def H_funnel(x,y):
    return (f'<g transform="translate({x},{y})"><g fill="none" stroke="{NV}" stroke-width="7" stroke-linejoin="round"><path d="M30 30 H230 L162 130 V200 L120 222 V130 Z"/></g>'
            f'<g><circle cx="64" cy="12" r="11" fill="{CO}"/><circle cx="110" cy="2" r="11" fill="{GR}"/><circle cx="158" cy="12" r="11" fill="{NV}"/><circle cx="200" cy="6" r="11" fill="{OR}"/><circle cx="130" cy="64" r="10" fill="{OR}"/></g>'
            f'<path d="M130 222 v34" stroke="{OR}" stroke-width="5"/>{badge_check(86,266,22)}'
            f'<g transform="translate(222,140)"><circle r="22" fill="{CO}"/><g transform="rotate(45)"><path d="M-10 0h20M0 -10v20" stroke="#fff" stroke-width="4.5" stroke-linecap="round"/></g></g></g>')
def H_moon(x,y):
    return (f'{moon(x+80,y+70,78)}{stars([(x-10,y-6,4),(x+200,y+14,3.4),(x+180,y+150,3),(x+10,y+150,3)])}'
            f'{clock(x+80,y+208,50)}{headset(x+186,y+196)}')
def H_missed(x,y):
    return (f'<g transform="translate({x},{y})"><circle cx="120" cy="150" r="128" fill="url(#glow)"/>'
            f'<rect x="58" y="30" width="164" height="246" rx="30" fill="{NV}"/><rect x="72" y="50" width="136" height="206" rx="20" fill="{CR}"/>'
            f'<g transform="rotate(135 140 122)"><circle cx="140" cy="122" r="36" fill="#FBE3DC"/><circle cx="140" cy="122" r="21" fill="{CO}"/>'
            f'<path d="M129 117c1 7 8 13 16 13 2 0 4-2 3-5l-1-6c-1-2-4-3-6-2l-3 1c-3-2-5-4-7-7l1-3c1-2 0-5-2-6l-6-2c-3-1-5 1-5 4z" fill="#fff"/></g>'
            f'<circle cx="176" cy="92" r="12" fill="{CO}"/><path d="M171 92h10M176 87v10" stroke="#fff" stroke-width="3" stroke-linecap="round"/>'
            f'<rect x="96" y="186" width="88" height="10" rx="5" fill="{NV}"/><rect x="96" y="208" width="60" height="10" rx="5" fill="#C9C3B6"/></g>')

# ---------- bespoke composition per post — 4 layouts each (seed%4) ----------
# v0 hero-right/supports-left · v1 hero-left/supports-right · v2 hero-centered split-A · v3 hero-centered split-B
def c_contractor(v=0):
    return [hub_funnel(560,330,1),
            hub_funnel(640,330,-1),
            hub_funnel(600,300,1)+badge_check(190,210,30),
            hub_funnel(600,372,-1)+missed_tag(150,470)][v%4]
def c_locksmith(v=0):
    return [H_lock(360,210)+moon(940,150,66)+card_booked(880,360),
            H_lock(700,210)+moon(200,160,66)+card_booked(170,360),
            H_lock(470,158)+moon(180,150,58)+card_booked(880,380),
            H_lock(470,250)+moon(950,140,58)+card_booked(150,360)][v%4]
def c_roofer(v=0):
    return [H_roof(520,150)+sun(960,150,60)+card_booked(150,300),
            H_roof(250,150)+sun(210,130,58)+card_booked(880,330),
            H_roof(420,120)+sun(180,150,56)+card_booked(880,360),
            H_roof(420,200)+sun(960,140,56)+card_booked(150,360)][v%4]
def c_electrician(v=0):
    return [H_electric(700,210)+sms(190,250)+card_booked(170,360)+spark(330,300,690,330),
            H_electric(320,210)+sms(840,250)+card_booked(860,360)+spark(840,330,510,330),
            H_electric(480,150)+sms(170,210)+card_booked(870,370)+spark(300,250,700,300),
            H_electric(480,250)+sms(840,210)+card_booked(160,380)+spark(820,260,700,320)][v%4]
def c_hvac(v=0):
    return [H_hvac(640,230)+missed_tag(180,210)+clock(290,360,40)+badge_check(980,470,26),
            H_hvac(300,230)+missed_tag(840,210)+clock(950,360,40)+badge_check(200,470,26),
            H_hvac(460,180)+missed_tag(150,200)+card_booked(880,360),
            H_hvac(460,255)+missed_tag(840,200)+card_booked(150,360)][v%4]
def c_plumber(v=0):
    return [H_plumb(560,200)+clock(950,160,48)+moon(180,150,58)+card_booked(840,380),
            H_plumb(380,200)+clock(230,170,48)+moon(980,150,58)+card_booked(180,380),
            H_plumb(480,160)+moon(180,150,58)+card_booked(880,380)+clock(960,420,44),
            H_plumb(480,250)+moon(960,150,58)+card_booked(150,380)+clock(240,420,44)][v%4]
def c_missed(v=0):
    return [H_missed(360,180)+spark(640,300,790,330)+card_booked(800,300)+missed_tag(180,170),
            H_missed(700,180)+spark(680,300,520,330)+card_booked(200,300)+missed_tag(840,170),
            H_missed(510,150)+missed_tag(160,190)+card_booked(870,360)+spark(700,300,860,380),
            H_missed(510,255)+missed_tag(850,190)+card_booked(150,360)+spark(560,360,300,420)][v%4]
def c_booking(v=0):
    return [H_cal(470,170)+estimate_doc(190,250)+badge_check(940,430,30),
            H_cal(500,170)+estimate_doc(880,250)+badge_check(230,430,30),
            H_cal(480,140)+estimate_doc(170,250)+card_booked(880,380),
            H_cal(480,255)+estimate_doc(880,255)+card_booked(150,400)][v%4]
def c_qualification(v=0):
    return [H_funnel(470,200)+card_booked(820,360)+missed_tag(150,200),
            H_funnel(560,200)+card_booked(180,360)+missed_tag(840,200),
            H_funnel(480,160)+missed_tag(150,200)+card_booked(880,370),
            H_funnel(480,250)+missed_tag(840,200)+card_booked(150,370)][v%4]
def c_afterhours(v=0):
    return [H_moon(470,150)+card_booked(820,360),
            H_moon(560,150)+card_booked(180,360),
            H_moon(460,120)+card_booked(870,380)+badge_check(200,220,30),
            H_moon(460,210)+card_booked(150,380)+badge_check(990,220,30)][v%4]

# ---------- dynamism helpers ----------
def dots(pts):
    cs=[OR,GR,CO,NV]
    return "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{cs[i%4]}" opacity=".9"/>' for i,(x,y,r) in enumerate(pts))
def flow(x1,y1,x2,y2,c=None,bend=-60):
    c=c or OR
    mx,my=(x1+x2)/2,(y1+y2)/2+bend
    ang_dx,ang_dy=x2-mx,y2-my
    import math as _m
    a=_m.atan2(ang_dy,ang_dx)
    p1=(x2-14*_m.cos(a-0.5),y2-14*_m.sin(a-0.5)); p2=(x2-14*_m.cos(a+0.5),y2-14*_m.sin(a+0.5))
    return (f'<path d="M{x1} {y1} Q {mx} {my} {x2} {y2}" fill="none" stroke="{c}" stroke-width="4" stroke-dasharray="2 10" stroke-linecap="round"/>'
            f'<path d="M{x2} {y2} L{p1[0]:.0f} {p1[1]:.0f} L{p2[0]:.0f} {p2[1]:.0f} Z" fill="{c}"/>')

# ---------- new hero motifs ----------
def H_chat(x,y):
    return (f'<g transform="translate({x},{y})">'
            f'<rect x="0" y="0" width="180" height="270" rx="32" fill="{NV}"/><rect x="14" y="20" width="152" height="230" rx="22" fill="{CR}"/>'
            f'<rect x="28" y="44" width="88" height="34" rx="12" fill="#E9E2D3"/>'
            f'<rect x="38" y="56" width="66" height="6" rx="3" fill="#B9AF9C"/>'
            f'<rect x="64" y="92" width="88" height="42" rx="12" fill="{OR}"/>'
            f'<rect x="74" y="104" width="66" height="6" rx="3" fill="#fff"/><rect x="74" y="116" width="44" height="6" rx="3" fill="#FBD9A8"/>'
            f'<rect x="28" y="148" width="70" height="30" rx="12" fill="#E9E2D3"/>'
            f'<circle cx="48" cy="163" r="4" fill="#B9AF9C"/><circle cx="63" cy="163" r="4" fill="#B9AF9C"/><circle cx="78" cy="163" r="4" fill="#B9AF9C"/>'
            f'<rect x="64" y="192" width="88" height="34" rx="12" fill="{GR}"/>'
            f'<rect x="74" y="202" width="60" height="6" rx="3" fill="#fff"/><rect x="74" y="213" width="40" height="5" rx="2.5" fill="#CFF2DE"/>'
            f'</g>')
def H_van(x,y):
    return (f'<g transform="translate({x},{y})">'
            f'<path d="M188 96 h-160 v-60 q0 -14 14 -14 h96 q12 0 18 10 l22 34 q10 4 10 14 z" fill="{CR}" stroke="{NV}" stroke-width="7" stroke-linejoin="round"/>'
            f'<path d="M140 30 l18 30 h-42 v-30 z" fill="{BL}" stroke="{NV}" stroke-width="5" stroke-linejoin="round"/>'
            f'<rect x="40" y="34" width="58" height="26" rx="8" fill="{BL}" stroke="{NV}" stroke-width="5"/>'
            f'<rect x="28" y="70" width="118" height="12" rx="6" fill="{OR}"/>'
            f'<circle cx="58" cy="100" r="20" fill="{NV}"/><circle cx="58" cy="100" r="8" fill="#fff"/>'
            f'<circle cx="150" cy="100" r="20" fill="{NV}"/><circle cx="150" cy="100" r="8" fill="#fff"/>'
            f'<path d="M30 12 h80" stroke="{OR}" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M-34 40 h24 M-46 62 h36 M-30 84 h20" stroke="{CO}" stroke-width="5" stroke-linecap="round" opacity=".85"/>'
            f'</g>')
def H_review(x,y):
    return (f'<g transform="translate({x},{y})">'
            f'<rect x="0" y="0" width="256" height="170" rx="22" fill="#fff" stroke="#EFE6D7" stroke-width="2.5"/>'
            f'<circle cx="46" cy="46" r="20" fill="{BL}"/><path d="M46 40 a7 7 0 1 1 0.1 0 M32 60 q14 -12 28 0" stroke="{NV}" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
            f'<rect x="78" y="32" width="92" height="9" rx="4.5" fill="{NV}"/><rect x="78" y="50" width="60" height="8" rx="4" fill="#C9C3B6"/>'
            f'<g transform="translate(30,86)">'
            + "".join(f'<path transform="translate({i*42},0) scale(1.5)" d="M12 2l2.6 5.3 5.9.8-4.3 4.1 1 5.8L12 15.3 6.8 18l1-5.8L3.5 8.1l5.9-.8z" fill="{OR if i<4 else "#E6DFD0"}"/>' for i in range(5)) +
            f'</g><rect x="30" y="138" width="150" height="8" rx="4" fill="#E6DFD0"/>'
            f'{badge_check(238,158,24)}</g>')
def H_chart(x,y):
    return (f'<g transform="translate({x},{y})">'
            f'<rect x="0" y="0" width="264" height="184" rx="22" fill="#fff" stroke="#EFE6D7" stroke-width="2.5"/>'
            f'<rect x="20" y="16" width="96" height="9" rx="4.5" fill="{NV}"/>'
            f'<g transform="translate(28,150)">'
            f'<rect x="0" y="-44" width="30" height="44" rx="6" fill="#F0C689"/>'
            f'<rect x="44" y="-70" width="30" height="70" rx="6" fill="{OR}"/>'
            f'<rect x="88" y="-56" width="30" height="56" rx="6" fill="{CO}"/>'
            f'<rect x="132" y="-96" width="30" height="96" rx="6" fill="{GR}"/>'
            f'<rect x="176" y="-118" width="30" height="118" rx="6" fill="{NV}"/></g>'
            f'<path d="M36 92 L86 72 L134 84 L196 34" fill="none" stroke="{NV}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity=".85"/>'
            f'<path d="M196 34 l-16 -2 m16 2 l-4 15" stroke="{NV}" stroke-width="4" stroke-linecap="round" opacity=".85"/>'
            f'</g>')

# ---------- new scene compositions (4 layouts each) ----------
def c_textchat(v=0):
    return [H_chat(430,150)+flow(640,300,820,350,GR)+card_booked(830,330)+dots([(300,200,5),(340,420,4),(910,210,5),(240,300,4)]),
            H_chat(590,150)+flow(560,300,370,350,GR,bend=-70)+card_booked(190,330)+dots([(880,220,5),(860,420,4),(300,210,5)]),
            H_chat(510,130)+missed_tag(170,220)+flow(380,260,500,220,CO,bend=40)+card_booked(860,370)+dots([(950,220,5),(260,430,4)]),
            H_chat(510,190)+card_booked(150,380)+flow(410,420,330,410,GR,bend=30)+badge_check(960,240,28)+dots([(920,420,5),(300,180,4)])][v%4]
def c_van(v=0):
    return [H_van(480,260)+sun(1000,140,56)+flow(300,400,460,350,OR,bend=-40)+card_booked(160,300)+dots([(900,430,5),(280,220,4)]),
            H_van(560,260)+sun(200,130,54)+flow(900,400,760,350,OR,bend=-40)+card_booked(870,290)+dots([(300,430,5),(950,220,4)]),
            H_van(500,230)+moon(180,150,56)+card_booked(860,350)+flow(720,330,850,380,GR,bend=-30)+dots([(280,350,5),(1000,200,4)]),
            H_van(500,300)+clock(230,200,44)+card_booked(880,380)+flow(320,260,470,320,CO,bend=-50)+dots([(940,240,5),(200,440,4)])][v%4]
def c_reviews(v=0):
    return [H_review(470,180)+flow(430,420,350,380,OR,bend=40)+card_booked(170,300)+dots([(900,230,5),(880,440,4),(300,470,4)]),
            H_review(480,180)+flow(760,420,850,380,OR,bend=40)+card_booked(860,300)+dots([(300,230,5),(320,440,4)]),
            H_review(450,150)+badge_check(240,240,30)+dots([(880,220,6),(940,320,4),(860,430,5),(260,420,4)]),
            H_review(490,240)+missed_tag(160,200)+flow(400,300,480,300,GR,bend=-40)+dots([(950,260,5),(900,450,4)])][v%4]
def c_report(v=0):
    return [H_chart(460,170)+flow(420,420,340,390,GR,bend=40)+card_booked(160,300)+dots([(900,240,5),(880,430,4)]),
            H_chart(480,170)+flow(770,420,860,390,GR,bend=40)+card_booked(860,300)+dots([(300,240,5),(320,430,4)]),
            H_chart(440,140)+badge_check(950,260,30)+dots([(260,240,6),(300,430,4),(980,430,5)]),
            H_chart(490,230)+clock(240,220,44)+card_booked(880,400)+dots([(950,220,5),(210,430,4)])][v%4]

COMPOSE={
 "best-lead-response-system-for-contractors":(c_contractor,False),
 "locksmith-after-hours-lead-response-that-wins":(c_locksmith,True),
 "roofer-inbound-lead-follow-up-automation":(c_roofer,False),
 "electrician-text-back-automation-that-books-jobs":(c_electrician,False),
 "hvac-missed-call-lead-recovery-that-books-jobs":(c_hvac,False),
 "24-7-ai-answering-service-for-plumbers":(c_plumber,True),
 "how-to-stop-losing-leads-from-missed-calls":(c_missed,False),
 "automated-estimate-booking-for-contractors":(c_booking,False),
 "ai-lead-qualification-for-home-services":(c_qualification,False),
 "after-hours-answering-service-for-contractors":(c_afterhours,True),
 "live-text-conversation-that-books":(c_textchat,False),
 "service-van-on-the-way":(c_van,False),
 "five-star-reviews-won":(c_reviews,False),
 "weekly-earnings-report":(c_report,False),
}
def scene(slug,v=0):
    fn,night=COMPOSE[slug]
    gx="82%" if v==0 else "18%"
    sky=('<ellipse cx="600" cy="150" rx="640" ry="220" fill="#2A3A57" opacity=".12"/>'+stars([(120,80,2.6),(1080,70,2.2),(60,150,2),(1040,150,2.4)])
         if night else f'<circle cx="{1010 if v==0 else 190}" cy="120" r="150" fill="#F4DFC2" opacity=".5"/>')
    return f'''<!doctype html><html><head><meta charset=utf-8><style>*{{margin:0}}svg{{display:block}}</style></head><body>
<svg width=1200 height=675 viewBox="0 0 1200 675" xmlns="http://www.w3.org/2000/svg">
<defs><radialGradient id="paper" cx="{gx}" cy="6%" r="120%"><stop offset="0" stop-color="#FDEAD0"/><stop offset="55%" stop-color="#FBF8F2"/></radialGradient>
<radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#F2960F" stop-opacity=".26"/><stop offset="70%" stop-color="#F2960F" stop-opacity="0"/></radialGradient></defs>
<rect width="1200" height="675" fill="url(#paper)"/>{sky}
{ground(330,180)}{ground(860,210)}
{fn(v)}
</svg></body></html>'''

POSTS=[
 {"id":7381,"media":7382,"slug":"best-lead-response-system-for-contractors"},
 {"id":7332,"media":7333,"slug":"locksmith-after-hours-lead-response-that-wins"},
 {"id":7295,"media":7296,"slug":"roofer-inbound-lead-follow-up-automation"},
 {"id":7244,"media":7245,"slug":"electrician-text-back-automation-that-books-jobs"},
 {"id":7239,"media":7240,"slug":"hvac-missed-call-lead-recovery-that-books-jobs"},
 {"id":7237,"media":7238,"slug":"24-7-ai-answering-service-for-plumbers"},
 {"id":7221,"media":7230,"slug":"how-to-stop-losing-leads-from-missed-calls"},
 {"id":7208,"media":7229,"slug":"automated-estimate-booking-for-contractors"},
 {"id":7182,"media":7228,"slug":"ai-lead-qualification-for-home-services"},
 {"id":7176,"media":7227,"slug":"after-hours-answering-service-for-contractors"},
]
def build(p):
    hp=os.path.join(OUT,f"{p['slug']}.html"); pp=os.path.join(OUT,f"{p['slug']}.png")
    open(hp,"w").write(scene(p["slug"]))
    subprocess.run([CHROME,"--headless","--disable-gpu","--hide-scrollbars","--force-device-scale-factor=2",
      "--window-size=1200,675","--virtual-time-budget=8000",f"--screenshot={pp}",f"file://{hp}"],
      stderr=subprocess.DEVNULL,check=True)
if __name__=="__main__":
    json.dump(POSTS,open(os.path.join(HERE,"posts.json"),"w"),indent=2)
    for p in POSTS:
        print("rendering",p["slug"]); build(p)
    print("done ->",OUT)
