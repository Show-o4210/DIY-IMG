# PVZH DIY 精选与公共素材

公共文本 icon 独立收录：**破甲**，引用 **`[khh]`**，见 [图标目录与添加说明](public-assets/text-icons/README.md)。原图 1254×1254 RGBA PNG 字节保留；图标的备注名 `name` 与嵌入名 `embed_key` 分开。图标发布入口为 [`public-assets/text-icons/catalog/index.json`](https://show-o4210.github.io/DIY-IMG/public-assets/text-icons/catalog/index.json)，普通素材入口保持不变。

**新增文本嵌入 icon 只放 `public-assets/text-icons/items/`，使用 `--text-icons` 单独生成和校验；普通素材继续放 `public-assets/items/`。禁止将 `TEXT_ICON` 放入旧目录，避免旧客户端读取。**

本仓库保留已归档的玩家精选，并管理可下载使用的公共素材。客户端源码不在本仓库，本仓库不是用户上传服务或通用图床。

公共素材位于 [public-assets](public-assets/README.md)，按用途分区、标签和固定 ID 管理，客户端直接从 GitHub 获取目录、缩略图和原图。当前普通目录为 **228 项 / 77 标签**，另有独立文字图标“破甲” `[khh]`；与下述玩家精选的内容、用途和发布链路独立。2026-10-27 新增 show 的英国套系共 29 项：25 项主体、4 项超能力徽章（SKILL），原图字节保留，供下载及卡牌创作使用。搜索“英国套系”“英国”或 UK 编号 / 名称可查找；此前法国套系 v2 继续保留。逐项使用范围见各条目。维护命令为 `python scripts/build_public_assets.py --build`，检查为 `python scripts/build_public_assets.py`。

## 玩家精选已归档（2026-10-23）

玩家精选停止收录和更新。移除精选入口的新版客户端不再提供玩家精选浏览与署名收藏；官方漫画《第 0 张卡》和 MAIN-01 / SEED-01 立绘迁入新版客户端的「工具中心 → 角色介绍」，仍随客户端离线提供，与本仓库玩家目录分开。

最后一期目录为 `players-002`，收录 show 的 5 张冬青系列作品（冬青皇帝、冬青导弹、快乐的冬青、快乐的单青、不快乐的冬青），保留原有顺序。`catalog.json`、`works/<id>/image.png`、作者署名与逐件授权记录保留原路径、内容及既有许可；历史资源提交为 [`92e8763497aa48268b3806674aa6deadec7bf89a`](https://github.com/Show-o4210/DIY-IMG/tree/92e8763497aa48268b3806674aa6deadec7bf89a)，既有固定 SHA 图片地址继续保留。

后端暂时保留 `/api/pvzh-diy/v1/featured/version.json` 和 `/api/pvzh-diy/v1/featured/manifest.json`，返回最后一期快照，供仍使用这些接口的旧版客户端兼容。此次归档不删除历史作品、改写许可或清除用户已经保存到相册的收藏。

归档仅针对玩家精选模块，仓库本身继续维护。根目录 `1.png` 仍是连通性测试样本，未确认作者授权，不属于正式精选，也未获本仓库统一许可。

## 文件
- `catalog.json`：原始精选信息、相对图片路径和逐件授权范围。
- `examples/work.pending.json`：待审核条目示例，不参与发布。
- `scripts/build_catalog.py`：验证授权、尺寸、大小，计算 SHA-256，生成 Render 快照。
- `LICENSE.md`：逐件授权规则；不存在适用于所有作品的 MIT 许可。

## 历史收录与发布流程
以下保留归档前的流程说明，不再用于日常新增或换期。

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
