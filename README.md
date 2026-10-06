# PVZH DIY 精选资源
这是 PVZH DIY 客户端玩家精选的公开资源目录，只收录维护者审核并获授权的作品。客户端源码不在本仓库，本仓库不是上传服务或通用图床。

官方作品随客户端发布，与此目录分开。当前正式玩家目录为空；根目录 `1.png` 是连通性测试样本，未确认作者授权，不属于正式精选，也未获本仓库统一许可。

## 文件
- `catalog.json`：原始精选信息、相对图片路径和逐件授权范围。
- `examples/work.pending.json`：待审核条目示例，不参与发布。
- `scripts/build_catalog.py`：验证授权、尺寸、大小，计算 SHA-256，生成 Render 快照。
- `LICENSE.md`：逐件授权规则；不存在适用于所有作品的 MIT 许可。

## 收录与发布
1. 作者告知署名、原图和授权范围。审核记录仅公开作者认可的摘要，聊天截图、联系方式等私密证据由维护者另存。
2. 把确认可公开的图片放在 `works/<id>/image.png`；填写 catalog 条目与授权摘要。未批准的条目只能留在 examples 或私有审核资料中；公开 Git 本身已构成传播，不得先上传未知授权作品再审核。
3. 修改 `featured_version`（图片、作者留言、授权或排序变化都要修改），验证目录并提交。
4. 用完整 40 位提交 SHA 生成快照，验证对应 CDN 图片能下载且 SHA 一致，再把生成文件替换 Render 的 `data/featured.json` 并部署：
   `python scripts/build_catalog.py --revision <SHA> --output <Render项目>/data/featured.json --verify-cdn`
5. Render 只读本地 JSON，不代拉 GitHub、不代理图片。客户端按当前页逐张请求 jsDelivr 并缓存，目录变更时复用哈希相同的文件。

单图上限 1 MiB，边长不超过 6000、像素不超过 1200 万；过大的原图在作者允许的前提下另行制作发布图，原图是否公开也需单独确认。最多 50 件当前精选，移除目录项即可使更新后的客户端停止展示；相册收藏不被删除。

## CDN 与撤回
本目录用于应用中的有限精选资源，而非为所有用户上传图片提供托管。公开文档和逐件许可明确允许的用户用途；不要求客户端源码开源，也不擅自改写作者许可。遵守 [jsDelivr 条款](https://github.com/jsdelivr/jsdelivr/blob/master/Terms%20of%20Use.md)，将来范围变化时重新评估用途。
CDN 的不可变资源可能在 GitHub 删除后继续保留，不承诺撤回后所有副本即时消失；在作者授权前明确告知公开 Git 历史、CDN 和用户相册缓存这一点。
