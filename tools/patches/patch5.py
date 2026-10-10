import os, sys
d = sys.argv[1] if len(sys.argv) > 1 else '.'
p = os.path.join(d, 'middleware.js')
s = open(p, encoding='utf-8').read()
old = 'function renderMetaPage({ title, description, image, url }) {'
assert s.count(old) == 1, s.count(old)
new = ("function __ogImage(image, url) {\n  try {\n    const u = new URL(url);\n    const m = u.pathname.match(/^\\/produit\\/([^/]+)/);\n    if (m) return u.origin + '/api/og?id=' + encodeURIComponent(decodeURIComponent(m[1]));\n    return u.origin + '/api/og';\n  } catch (e) { return image; }\n}\n" + old + "\n  image = __ogImage(image, url);")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
print('ok5')
