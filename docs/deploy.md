# 部署到一台服务器（纯静态 + 隧道）

本站没有任何后端：nginx 吐文件，TLS 由 nginx 自己终结，外部流量从 natfrp 的
HTTPS 隧道进来。

```
浏览器 ──TLS──> natfrp 节点(node 59) ──原样透传 TLS──> 127.0.0.1:8080
                                                       │
                              nginx 容器 (:443, 用 deploy/certs 的证书)
                                                       │
                                              ./web 挂载为只读卷
```

## 关键事实：隧道不终结 TLS

这是上线时踩的坑，值得单独写一段。natfrp 的 `https` 类型隧道在节点上**不做 TLS
终结**，它把客户端发来的 TLS 字节原样转发给本地端口。证据是：把 ClientHello 发到
`keymap.ayeez.cn:443` 之后，nginx 的 access log 里出现了一条裸的

```
"\x16\x03\x01\x06$\x01\x00\x06 \x03\x03..." 400 150
```

也就是 nginx 把 TLS 记录当成 HTTP 请求收下并回了 400。所以本地必须自己终结 TLS。

（`ventrue1.ayeez.cn` 那条隧道能出现在浏览器里、并且带 SakuraFrp 自签证书，是因为
frpc 会在工作目录里给域名自动生成自签证书 —— 但那套机制对新建的 keymap 隧道没有
触发，最终就用 nginx 自己签的证书解决。）

## 步骤

```bash
# 1. 同步文件（远端目录要先存在，rsync 不会替你建父目录）
ssh ayeez@<host> 'mkdir -p ~/keymap-atlas/deploy ~/keymap-atlas/web'
rsync -az deploy/ ayeez@<host>:keymap-atlas/deploy/
rsync -az web/    ayeez@<host>:keymap-atlas/web/

# 2. 证书：放 deploy/certs/keymap.ayeez.cn.crt 与 .key
#    自签（浏览器会警告，先跑通链路）：
openssl req -x509 -newkey rsa:2048 -sha256 -days 825 -nodes \
  -keyout deploy/certs/keymap.ayeez.cn.key \
  -out    deploy/certs/keymap.ayeez.cn.crt \
  -subj "/CN=keymap.ayeez.cn" \
  -addext "subjectAltName=DNS:keymap.ayeez.cn" \
  -addext "keyUsage=digitalSignature,keyEncipherment" \
  -addext "extendedKeyUsage=serverAuth"

# 3. 起服务
cd ~/keymap-atlas/deploy && docker compose up -d

# 4. 验证（本机）
curl -k -sS -o /dev/null -w '%{http_code}\n' https://127.0.0.1:8080/
curl    -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8081/healthz
```

端口约定：`8080` 映射到容器 443（隧道目标），`8081` 映射到容器 80（本机明文调试）。

## 换成正式证书

用户已备案，后续申请 DV 证书后只需：

```bash
# 把 fullchain 与私钥覆盖进 deploy/certs/（文件名保持不变）
docker compose restart web
```

nginx 配置不用改。若证书文件名不同，改 `deploy/nginx.conf` 里的两行
`ssl_certificate` / `ssl_certificate_key` 即可。

换完用这条确认链是否完整（`Verify return code: 0 (ok)`）：

```bash
openssl s_client -connect keymap.ayeez.cn:443 -servername keymap.ayeez.cn </dev/null \
  | grep -E 'subject=|issuer=|Verify return code'
```

## 广告怎么填

广告代码已经在 `web/ad.js` 里，但**默认全部关闭**：`CFG` 里的 ID 为空时，
`guard()` 会在 8 秒后把广告位还原成 `data-filled="0"`，CSS 让它们 `display:none`，
页面上不留任何空洞。

填三个值即可上线：

```js
const CFG = {
  adsenseClient: "ca-pub-XXXXXXXXXXXXXXXX",   // AdSense 后台的发布商 ID
  slots: { top: "1234567890", mid: "0987654321" },  // 两条广告单元的 data-ad-slot
  adsterra: {
    top: { key: "xxxxxxxxxxxxxxxx", width: 728, height: 90 },
    mid: { key: "yyyyyyyyyyyyyyyy", width: 300, height: 250 },
  },
  ...
```

然后 `web/ads.txt` 里把占位行换成真行：

```
google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
```

Adsterra 不提供公开的 `ads.txt` 记录（实测 `adsterra.com/ads.txt` 返回的是网页，
不是纯文本），拿到 Publisher ID 后按它后台给的格式补一行。

### 只放固定尺寸 Banner 的理由

Adsterra 的 Popunder 会在用户点页面任意位置时开新窗口，直接触发 AdSense 的
「鼓励意外点击」违规；Social Bar 会劫持返回键、改页面标题，伤 SEO。两者都不要。
固定尺寸 Banner 是唯一能和安全并列的形式。每页 2–3 个位置足够，不要更多。

Cloudflare 的 Rocket Loader 会打乱 `invoke.js` 的执行顺序，所以加载器给
`<script>` 加了 `data-cfasync="false"`。

## 运维

```bash
docker compose ps                    # 状态与健康检查
docker compose logs --tail 50 web    # nginx 访问/错误日志
docker compose restart web           # 只重启网页
docker compose down                  # 停掉（证书与页面卷不受影响）
```

nginx 日志里如果又出现 `\x16\x03\x01` 被回 400，说明 TLS 又被透传到了明文端口，
检查 `docker-compose.yml` 的端口映射是否还是 `8080:443`。
