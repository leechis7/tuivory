"""Small ANSI cell reader for ASCII/border component regression output (no graphics dependency)."""
import re,unicodedata

def read_cells(text):
    x=y=0;pos=0;cells={};fg='7';bg='0';bold=dim=underline=False
    while pos<len(text):
        if text.startswith('\x1b[',pos):
            m=re.match(r'\x1b\[([0-?]*)([ -/]*)([@-~])',text[pos:])
            if not m:raise ValueError('incomplete ANSI sequence')
            params,_,command=m.groups();pos+=m.end()
            if params.startswith('?'):continue
            args=[int(v or 0)for v in params.split(';')]
            if command in ('H','f'):y=(args[0]or 1)-1;x=(args[1]or 1)-1 if len(args)>1 else 0
            elif command=='m':
                i=0
                while i<len(args):
                    c=args[i]
                    if c==0:fg='7';bg='0';bold=dim=underline=False
                    elif c==1:bold=True
                    elif c==2:dim=True
                    elif c==4:underline=True
                    elif c==22:bold=dim=False
                    elif c==24:underline=False
                    elif 30<=c<=37:fg=str(c-30)
                    elif 40<=c<=47:bg=str(c-40)
                    elif 90<=c<=97:fg=str(c-90+8)
                    elif 100<=c<=107:bg=str(c-100+8)
                    elif c in (38,48):
                        if args[i+1]==5:value=str(args[i+2]);i+=2
                        elif args[i+1]==2:value='#%02x%02x%02x'%tuple(args[i+2:i+5]);i+=4
                        else:raise ValueError('unknown color sequence')
                        if c==38:fg=value
                        else:bg=value
                    i+=1
            continue
        ch=text[pos];pos+=1
        if ch=='\r':x=0;continue
        if ch=='\n':y+=1;continue
        if unicodedata.combining(ch):continue
        if ord(ch)<32:continue
        width=2 if unicodedata.east_asian_width(ch)in('W','F')else 1
        cells[x,y]=(ch,fg,bg,bold,dim,underline)
        if width==2:cells[x+1,y]=('',fg,bg,bold,dim,underline)
        x+=width
    return cells


def complete_frame(data):
    """Return the latest complete Canvas frame, excluding prompts/cursor trailers.

    A status label can arrive before later rows and their final reset. Never
    decode a UTF-8 chunk or inspect SGR attributes until that frame is complete.
    """
    start=data.rfind(b'\x1b[?25l')
    if start<0:return None
    end=data.find(b'\x1b[0m',start)
    return bytes(data[start:end+4])if end>=0 else None


def check_fragmented_frames():
    frame=b'\x1b[?25l\x1b[1;1H\x1b[0;37;44m'+"가".encode()+b'\x1b[0m'
    for n in range(len(frame)):
        assert complete_frame(frame[:n])is None,n
    assert complete_frame(frame)==frame
    assert read_cells(complete_frame(frame).decode())[0,0][0:3]==('가','7','4')
    assert complete_frame(frame+b'\x1b[?25l\x1b[1;1H')is None
    assert complete_frame(frame+frame)==frame
    assert complete_frame(frame+b'\x1b[19;1H\x1b[K> ')==frame
    print('Fragmented UTF-8/SGR and complete Canvas frame boundaries passed')

if __name__=='__main__':check_fragmented_frames()
