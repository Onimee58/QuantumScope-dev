"""Viewport-independent vector PDF exports for QuantumScope circuits."""
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPdfWriter, QPainter, QColor, QPen, QFont, QPageSize
from quantumscope.physics.circuits import evolution
from quantumscope.physics.gate_education import angle_text
from quantumscope.physics.initial_states import defaults, product_state

def write_circuit_pdf(filename,n,gates,measurements,include_report=False,initial_states=None,blocks=(),noise=None,classical=None,conditions=None,labels=None):
    """Render the full circuit with scalable Qt vector primitives, not a screenshot.
    Each wire is labeled with its initial state (|0⟩ unless given). blocks are
    BlockPlacement objects: collapsed ones draw as labeled boxes, expanded ones
    as their gates inside a dashed outline."""
    from quantumscope.physics.blocks import placed_items
    initial_states=list(initial_states) if initial_states is not None else defaults(n)
    blocks=list(blocks)
    ordered=[g for *_,g,_ in placed_items(((r,c,g) for (r,c),g in gates.items()),blocks)]
    gates=dict(gates)
    for pl in blocks:
        if pl.expanded:
            gates.update({(g.targets[0],c):g for g,c in pl.placed_gates()})
    noise=dict(noise or {})
    classical=dict(classical or {})                   # (row, col) -> Measure or Reset
    conditions=dict(conditions or {})                 # gate key (row, col) -> (cbit, value)
    columns=max([c for _,c in gates]+list(measurements.values())+[pl.end for pl in blocks]+[c for _,c in noise]
                +[c for _,c in classical],default=0)+1
    writer=QPdfWriter(str(filename));writer.setResolution(96)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A3))
    painter=QPainter(writer)
    if not painter.isActive():raise OSError('Could not open PDF output')
    try:
        width=writer.width();height=writer.height()
        margin=48
        lane=72
        available=width-2*margin-125
        segments,scale=column_segments(columns,available,blocks)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0,0,width,height,QColor('white'))
        painter.setPen(QColor('#152536'));painter.setFont(QFont('Sans',17,QFont.Weight.Bold))
        painter.drawText(margin,65,'QuantumScope Circuit')
        painter.setFont(QFont('Sans',9))
        painter.drawText(margin,90,f'{n} qubits   •   {len(ordered)} unitary gates'+(f' ({len(blocks)} blocks)' if blocks else '')+f'   •   {len(measurements)} terminal measurements'
                         +(f'   •   {columns} columns, in {len(segments)} parts' if len(segments)>1 else ''))
        segment_height=part_height(n,scale,len(segments))
        top=125
        for c0,c1 in segments:
            if top+segment_height>height-margin and top>125:   # the next part does not fit: a new page
                writer.newPage();top=margin+20
                painter.fillRect(0,0,width,height,QColor('white'))
            if len(segments)>1:
                painter.setPen(QColor('#5b6b7a'));painter.setFont(QFont('Sans',8))
                painter.drawText(margin,top+8,f'Columns {c0+1}–{c1} of {columns}')
            painter.save();painter.translate(margin+95,top+(22 if len(segments)>1 else 0));painter.scale(scale,scale)
            painter.translate(-110*c0,0)
            _draw_part(painter,c0,c1,n,lane,initial_states,labels,gates,blocks,noise,classical,conditions,measurements)
            painter.restore()
            top+=segment_height
        if include_report:
            state=evolution(n,ordered,product_state(initial_states))[-1]
            probs=abs(state)**2
            order=sorted(range(len(probs)),key=lambda i:-probs[i])[:16]
            painter.setPen(QColor('#152536'));painter.setFont(QFont('Sans',11,QFont.Weight.Bold))
            y=top+30
            if y+310>=height:
                writer.newPage();y=70
            painter.drawText(margin,y,'Final state probabilities (up to 16 largest outcomes)')
            painter.setFont(QFont('Sans',10))
            for index in order:
                if probs[index]<1e-11:continue
                y+=20
                from quantumscope.physics.display import ket
                painter.drawText(margin,y,f'{ket(index,n,True)}    {100*probs[index]:.4f}%')
            y+=30
            if y+30<height:
                painter.drawText(margin,y,'Terminal measurements: '+(', '.join('q'+str(q) for q in sorted(measurements)) if measurements else 'none'))
    finally:
        painter.end()


def part_height(n,scale,parts,lane=72):
    """Height of one part of the drawing, with the gap below it."""
    return int((35+(n-1)*lane+35)*scale)+(28 if parts>1 else 0)


def pages_needed(n,columns,blocks=()):
    """How many A3 pages write_circuit_pdf will use for the drawing (the report may add one)."""
    width,height,margin=1123,1587,48                 # A3 at 96 dpi, as written
    parts,scale=column_segments(columns,width-2*margin-125,blocks)
    step=part_height(n,scale,len(parts))
    first=max(1,(height-margin-125)//step)
    later=max(1,(height-margin-(margin+20))//step)
    return 1 if len(parts)<=first else 1+-(-(len(parts)-first)//later)


MIN_SCALE=0.6                                   # wider circuits are split into parts, never drawn smaller


def column_segments(columns,available,blocks=()):
    """Split the columns into parts [c0, c1) that each fit `available` pixels at a readable scale,
    never breaking inside a block. Returns (parts, scale)."""
    full=max(400,columns*110)
    if available/full>=MIN_SCALE:                     # it fits on one line, as before
        return [(0,columns)],min(1.0,available/full)
    per=max(1,int(available/(110*MIN_SCALE)))
    inside=[(pl.col,pl.end) for pl in blocks]
    parts=[];c0=0
    while c0<columns:
        c1=min(columns,c0+per)
        if c1<columns:
            moved=c1
            while moved>c0+1 and any(a<moved<=b for a,b in inside):moved-=1
            if moved>c0+1:c1=moved
        parts.append((c0,c1));c0=c1
    return parts,min(1.0,available/(per*110))


def _draw_part(painter,c0,c1,n,lane,initial_states,labels,gates,blocks,noise,classical,conditions,measurements):
    """Draw columns c0 ≤ c < c1: the wires, their labels, and what starts in those columns."""
    def inside(c):return c0<=c<c1
    left,right=110*c0,110*c1
    painter.setFont(QFont('Sans',12))
    for q in range(n):
        y=35+q*lane
        painter.setPen(QPen(QColor('#273c4e'),2))
        state=initial_states[q]
        name=(list(labels or [])+['']*n)[q]
        painter.drawText(left-92,y+5,f'q{q}  {state.label}')
        if name:                                   # the qubit's label, small, above its name
            painter.setFont(QFont('Sans',8));painter.drawText(left-92,y-10,name);painter.setFont(QFont('Sans',12))
        if state.preset_key is None:
            painter.setFont(QFont('Sans',8))
            painter.drawText(left-92,y+21,f'θ={angle_text(state.theta)}, φ={angle_text(state.phi)}')
            painter.setFont(QFont('Sans',12))
        painter.drawLine(left,y,right,y)
    for (r,c),gate in sorted(((k,g) for k,g in gates.items() if inside(k[1])),key=lambda x:(x[0][1],x[0][0])):
        x=55+110*c;y=35+lane*r
        if len(gate.targets)>1:
            ys=[35+lane*q for q in gate.targets]
            painter.setPen(QPen(QColor('#2c5974'),2));painter.drawLine(x,min(ys),x,max(ys))
            for q in gate.targets[:-1]:
                painter.setBrush(QColor('#2c5974'));painter.drawEllipse(QRectF(x-5,35+lane*q-5,10,10))
        if gate.name in ('CX','CCX'):
            y=35+lane*gate.targets[-1]
            painter.setPen(QPen(QColor('#116182'),2));painter.setBrush(QColor('white'))
            painter.drawEllipse(QRectF(x-12,y-12,24,24));painter.drawLine(x-9,y,x+9,y);painter.drawLine(x,y-9,x,y+9)
        elif gate.name in ('SWAP','CSWAP'):
            for q in (gate.targets if gate.name=='SWAP' else gate.targets[1:]):
                yy=35+lane*q;painter.drawLine(x-8,yy-8,x+8,yy+8);painter.drawLine(x+8,yy-8,x-8,yy+8)
        elif gate.name in ('CZ','CP'):
            yy=35+lane*gate.targets[-1];painter.setBrush(QColor('#2c5974'));painter.drawEllipse(QRectF(x-5,yy-5,10,10))
            if gate.name=='CP':
                painter.setFont(QFont('Sans',9));painter.setPen(QColor('#12658b'))
                painter.drawText(QRectF(x+6,(35+lane*min(gate.targets)+yy)/2-10,60,20),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,'P('+angle_text(gate.angle)+')')
                painter.setFont(QFont('Sans',12))
        else:
            painter.setPen(QPen(QColor('#12658b'),2));painter.setBrush(QColor('#eff8fc'))
            rect=QRectF(x-26,y-22,52,44);painter.drawRoundedRect(rect,4,4)
            painter.drawText(rect,Qt.AlignmentFlag.AlignCenter,gate.name)
            if gate.name in ('RX','RY','RZ','P','U','CP'):
                painter.setFont(QFont('Sans',8));painter.drawText(QRectF(x-48,y+23,96,18),Qt.AlignmentFlag.AlignCenter,f'{gate.angle:.3g} rad');painter.setFont(QFont('Sans',12))
    for pl in (pl for pl in blocks if inside(pl.col)):
        top=35+lane*pl.block.low-30;bottom=35+lane*pl.block.high+30
        left=55+110*pl.col-45;right=55+110*pl.end+45
        if pl.expanded:
            painter.setPen(QPen(QColor('#7a62c9'),1.5,Qt.PenStyle.DashLine));painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(left,top,right-left,bottom-top),8,8)
            painter.setFont(QFont('Sans',9));painter.setPen(QColor('#4b3299'))
            painter.drawText(QRectF(left+6,top-18,right-left,16),Qt.AlignmentFlag.AlignLeft,pl.block.label)
            painter.setFont(QFont('Sans',12))
        else:
            painter.setPen(QPen(QColor('#5a3eb4'),2));painter.setBrush(QColor('#ebe5fb'))
            box=QRectF(left+12,top+8,right-left-24,bottom-top-16)
            painter.drawRoundedRect(box,6,6);painter.setPen(QColor('#2b1869'))
            painter.drawText(box,Qt.AlignmentFlag.AlignCenter,pl.block.label)
    for (q,c),element in ((k,e) for k,e in noise.items() if inside(k[1])):         # noise channels: dashed orange boxes
        x=55+110*c;y=35+lane*q
        painter.setPen(QPen(QColor('#b5600a'),1.5,Qt.PenStyle.DashLine));painter.setBrush(QColor('#fff4e6'))
        painter.drawRoundedRect(QRectF(x-30,y-20,60,40),6,6)
        painter.setPen(QColor('#7a3f00'));painter.setFont(QFont('Sans',9))
        short={'bit_flip':'BF','phase_flip':'PF','depolarizing':'DEP','amplitude_damping':'AD','phase_damping':'PD'}[element.kind]
        painter.drawText(QRectF(x-30,y-20,60,40),Qt.AlignmentFlag.AlignCenter,f'{short}\n{element.p:g}')
        painter.setFont(QFont('Sans',12))
    for (q,c),item in ((k,i) for k,i in classical.items() if inside(k[1])):         # mid-circuit measurements (M→c) and resets
        x=55+110*c;y=35+lane*q
        measure=hasattr(item,'cbit')
        painter.setPen(QPen(QColor('#b06a00') if measure else QColor('#2f4f6f'),2))
        painter.setBrush(QColor('#fff4dc') if measure else QColor('#e8f1f8'))
        painter.drawRoundedRect(QRectF(x-30,y-20,60,40),6,6)
        painter.setPen(QColor('#3d2a00') if measure else QColor('#1b3550'));painter.setFont(QFont('Sans',9))
        painter.drawText(QRectF(x-30,y-20,60,40),Qt.AlignmentFlag.AlignCenter,
                         f'M\n→c{item.cbit}' if measure else '|0⟩\nreset')
    for (q,c),(cbit,value) in ((k,v) for k,v in conditions.items() if inside(k[1])):  # 'if c = v' badges above conditioned gates
        gate=gates.get((q,c))
        if gate is None:continue
        x=55+110*c;y=35+lane*gate.targets[-1]
        painter.setPen(QPen(QColor('#b06a00'),1));painter.setBrush(QColor('#fff4dc'))
        painter.drawRoundedRect(QRectF(x-26,y-34,52,14),4,4)
        painter.setPen(QColor('#3d2a00'));painter.setFont(QFont('Sans',8))
        from quantumscope.physics.dynamic import condition_text
        painter.drawText(QRectF(x-26,y-34,52,14),Qt.AlignmentFlag.AlignCenter,condition_text(cbit,value).replace(' ',''))
    painter.setFont(QFont('Sans',12))
    for q,c in ((q,c) for q,c in measurements.items() if inside(c)):
        x=55+110*c;y=35+lane*q
        painter.setPen(QPen(QColor('#ae7221'),2));painter.setBrush(QColor('#fff4dc'))
        rect=QRectF(x-25,y-22,50,44);painter.drawRoundedRect(rect,4,4)
        painter.drawText(rect,Qt.AlignmentFlag.AlignCenter,'M')
