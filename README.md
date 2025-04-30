# Hunyuan3D-2 と SyncMVD を使ったテクスチャ付き3Dメッシュの作成支援ツール

Hunyuan3D-2でメッシュ生成（※）、SyncMVDでテクスチャ合成する場合、それぞれを個別に呼び出すのはそれなりに手間なので、1コマンドで使えるようにしただけです。

※ 本来、Hunyuan3D-2ではメッシュ合成もできますが、ここではメッシュ生成だけを利用します

## 🔧 動作条件

本ツールは以下の外部ソフトウェアを subprocess 経由で使用します：

- [Hunyuan3D-2](https://github.com/Tencent/Hunyuan3D-2)：Tencent Hunyuan 3D 2.0 Community License
- [SyncMVD](https://github.com/LIU-Yuxin/SyncMVD) ：MIT License  

それぞれのライセンス条項に従ってご利用ください。Hunyuan3D-2 は特に注意が必要です。

（Hunyuan3D-2 と SyncMVD はそれぞれ Conda 環境で用意してください。 本ツールはPythonの標準ライブラリしか使わないのでLinuxディストリビューションのPythonで問題ありません。）

## 📦 本ツールのディレクトリ構成

```
project_root/
├── tkg_textured_mesh_gen.py         # メインスクリプト
├── config.yaml                      # 環境設定ファイル（要変更）
├── README.md                        # この説明書
├── LICENSE                          # ライセンス情報
└── external/
    └── tkg_image2mesh.py            # Hunyuan3D-2 にコピーして使用
```

## ① 最初にすること

`tkg_image2mesh.py` を Hunyuan3D-2 の直下にコピーする。

## ② `config.yaml` の設定



```yaml
hunyuan:
  dir: "/home/<USER_NAME>/Hunyuan3D-2"
  conda_python: "/home/<USER_NAME>/miniconda3/envs/hunyuan3d/bin/python"
  script: "tkg_image2mesh.py"

syncmvd:
  dir: "/home/<USER_NAME>/SyncMVD"
  conda_python: "/home/<USER_NAME>/miniconda3/envs/syncmvd/bin/python"
  script: "run_experiment.py"
```

### 🔸ヒント：
- 自分の環境に合わせて書き換えてください。
- SyncMVD のスクリプトは `run_experiment.py` （←SyncMVD側で用意しているファイル）となっていますが適宜変更してください。画像生成時のチェックポイントやVAEを変えるなど、run_experiment.py を改変して使っている場合はそのファイル名を指定してください）。

## 🚀 簡単な使い方

2通りの使い方があります。
   
### ① Hunyuan3D-2でメッシュ生成，SyncMVDでテクスチャを合成を行う場合

```bash
python tkg_textured_mesh_gen.py \
  --input-image input.png \
  --output-mesh mymesh.glb \
  --prompt "a photo of ......"
```

--prompt は SyncMVDに渡すプロンプトです．また，--seedなども設定できます（--helpで確認）．

### ② 生成済みメッシュを使って，SyncMVDでテクスチャ合成のみ行う場合

```bash
python tkg_textured_mesh_gen.py \
  --input-mesh mymesh.glb \
  --prompt "a photo of ......"
```


 
