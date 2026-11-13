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

证书商给的压缩包里通常有四个文件：

```
keymap.ayeez.cn.csr          申请时用的，服务器上不需要
keymap.ayeez.cn.key          私钥，保密
keymap.ayeez.cn_bundle.crt   叶证书 + 中间 CA + 根证书（三张）
keymap.ayeez.cn_bundle.pem   和上面的 .crt 内容相同，二选一
```

**nginx 的 `ssl_certificate` 只要「叶 + 中间」，不要根证书。** 根证书在
所有系统信任库里本来就有，拼进去只会增加握手体积（这张多 2138 字节）。
先把 bundle 按 `BEGIN CERTIFICATE` 拆开，取前两张拼成 fullchain：

```bash
cd /tmp && mkdir -p ssl && cd ssl
unzip ~/keymap.ayeez.cn_other.zip
cd keymap.ayeez.cn_other

# 拆成 cert1/cert2/cert3（叶 / 中间 / 根）
awk 'BEGIN{n=0} /BEGIN CERTIFICATE/{n++} {print > ("cert" n ".crt")}' \
    keymap.ayeez.cn_bundle.crt

# 前两张拼成 fullchain
awk 'BEGIN{n=0} /BEGIN CERTIFICATE/{n++} n<=2 {print}' \
    keymap.ayeez.cn_bundle.crt > fullchain.crt

# 确认是两张，且第一张是叶证书
grep -c "BEGIN CERTIFICATE" fullchain.crt          # 2
openssl x509 -in fullchain.crt -noout -subject     # CN=keymap.ayeez.cn

# 确认私钥和证书是一对（两个 md5 必须相同）
openssl x509 -in cert1.crt -noout -modulus | openssl md5
openssl rsa  -in keymap.ayeez.cn.key -noout -modulus | openssl md5
```

然后替换服务器上那两个文件（**文件名保持不变**，配置里写死了）：

```bash
scp fullchain.crt ayeez@<server>:~/keymap-atlas/deploy/certs/keymap.ayeez.cn.crt
scp keymap.ayeez.cn.key ayeez@<server>:~/keymap-atlas/deploy/certs/keymap.ayeez.cn.key

ssh ayeez@<server> 'cd ~/keymap-atlas/deploy \
  && chmod 644 certs/keymap.ayeez.cn.crt && chmod 600 certs/keymap.ayeez.cn.key \
  && docker compose restart web'
```

nginx 配置不用改。若证书文件名不同，改 `deploy/nginx.conf` 里的两行
`ssl_certificate` / `ssl_certificate_key` 即可。

换完用这两条确认（`Verify return code: 0 (ok)` 且链里能看到中间 CA）：

```bash
openssl s_client -connect keymap.ayeez.cn:443 -servername keymap.ayeez.cn </dev/null \
  | grep -E 'subject=|issuer=|Verify return code'

# 链的层数：应该能看到叶证书和中间 CA 两段 s:/
openssl s_client -connect keymap.ayeez.cn:443 -servername keymap.ayeez.cn </dev/null \
  | grep -E '^\s+[0-9]+ s:|^\s+i:'
```

`sslv2`/`sslv3` 还没关（nginx 默认就不听这些），`TLSv1.2` 以下已经禁用，
`ssl_session_tickets off` 是为了在换证书时立刻失效旧会话。

### 证书到期

TrustAsia DV 证书有效期三个月。到期前在控制台续期，续期后重复上面这套替换
流程即可——**配置和容器都不用重建**，只要覆盖两个文件再 `restart`。

到期检查：

```bash
echo | openssl s_client -connect keymap.ayeez.cn:443 -servername keymap.ayeez.cn 2>/dev/null \
  | openssl x509 -noout -enddate
```

## 运维

```bash
docker compose ps                    # 状态与健康检查
docker compose logs --tail 50 web    # nginx 访问/错误日志
docker compose restart web           # 只重启网页
docker compose down                  # 停掉（证书与页面卷不受影响）
```

nginx 日志里如果又出现 `\x16\x03\x01` 被回 400，说明 TLS 又被透传到了明文端口，
检查 `docker-compose.yml` 的端口映射是否还是 `8080:443`。
