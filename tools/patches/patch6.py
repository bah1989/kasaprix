import re,sys,json
# middleware: extension-style image URL + size/type tags
p='middleware.js'
s=open(p,encoding='utf-8').read()
a="'/api/og?id=' + encodeURIComponent(decodeURIComponent(m[1]))"
b="'/api/og'"
n=0
if a in s:
    s=s.replace(a,"'/og/' + encodeURIComponent(decodeURIComponent(m[1])) + '.jpg'");n+=1
# default image (only the helper's default, not the product one already replaced)
s2=s.replace("return u.origin + '/api/og';","return u.origin + '/og/default.jpg';")
if s2!=s:n+=1
s=s2
def addtags(m):
    line=m.group(0)
    mm=re.search(r'content="([^"]*)"',line)
    if not mm: return line
    u=mm.group(1)
    return line+'\n<meta property="og:image:secure_url" content="'+u+'">\n<meta property="og:image:type" content="image/jpeg">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">'
# template literal may use ${...}; handle both
pat=re.compile(r'<meta property="og:image" content="[^"\n]*">')
s3,k=pat.subn(addtags,s)
if k:
    s=s3;n+=1
open(p,'w',encoding='utf-8').write(s)
# og.js: explicit length + long cache
p='api/og.js'
o=open(p,encoding='utf-8').read()
o=o.replace("res.setHeader('Cache-Control', 'public, s-maxage=3600, stale-while-revalidate=86400');","res.setHeader('Cache-Control', 'public, max-age=86400, s-maxage=86400, stale-while-revalidate=604800');\n  res.setHeader('Content-Length', String(out.length));")
open(p,'w',encoding='utf-8').write(o)
print('patch6 changes',n,'metaTags',k)
