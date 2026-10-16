# 热拉公共资源

本目录独立于根目录的玩家精选。资源信息、预览和原图均由客户端直接从本 GitHub 仓库获取，不通过 Render 或 jsDelivr。当前仅收录维护工具生成、明确标注的占位示例，不代表正式素材内容。

## 添加与修改

1. 在 `items/<固定ID>/` 放入 `original.png` 或 `original.jpg`，新增 `info.json`，参考现有占位示例。ID 一经使用不要修改或分配给另一资源。
2. 填写 `name`、`category`、`tags`、`author`、`source_url`、`usage`、`description`、`aliases` 和 `file`。标签引用 `tags.json` 中的 ID，显示时客户端添加 `#`；同义词放在标签 aliases，不重复创建同义标签。
3. 运行 `python scripts/build_public_assets.py --build`，自动生成缩略图、原图 / 缩略图哈希文件与客户端目录；运行 `python scripts/build_public_assets.py` 和 `python -m unittest discover -s tests -v` 校验。
4. 提交原图、说明、缩略图、生成文件和目录。协作者通过 PR 提交，由维护者审核合并。公开前先确认素材可用于下载、创作及对应分享用途；精选的展示授权不自动扩展到素材再利用。

分区：`SUBJECT` 主体、`FRAME` 卡框、`RIBBON` 彩带、`BACKGROUND` 底图、`PATTERN` 图案、`STICKER` 贴纸、`COST` 消耗、`ATTACK` 攻击、`HEALTH` 生命、`HERO_TYPE` 属性标志、`SKILL` 技能、`TEXT_ICON` 文字图标。彩带 `ribbon_scope` 为 `CARD` / `HERO` / `COMMON`，缺省通用。原图支持 PNG / JPEG，32 MiB、4000 万像素以内。

## 发布与回退

`catalog/index.json` 指向哈希命名的不可变目录，目录再指向 `files/<sha256>.<format>`。先提交完整生成文件再更新索引；脚本完成这两步，客户端校验目录及每张图片的哈希与尺寸。只改说明 / 标签会换目录版本；原图变化会换资源 revision，同 ID 的旧原图仍保留。

不要修改或清理已经发布的 `files/` 和 `catalog/manifests/`，旧客户端缓存的目录可能仍引用它们。下架时移走对应 `items/<ID>` 输入并重新生成目录，已加入用户本地仓库的文件不删除。回退时恢复上一版 `catalog/index.json` 即可，后续再次发布前以当前 inputs 重新生成并核对。

全部图片使用原始内容校验；本地改名不影响资源身份。客户端保留本地用途 / 名称，不自动覆盖已有图像，用户主动添加新版后旧文件及旧作品引用继续保留。来源和使用说明随下载保存为本地可选信息，不依赖缓存目录永久存在。
