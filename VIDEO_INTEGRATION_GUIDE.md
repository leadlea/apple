# 🎬 動画統合ガイド - Mac Status PWA

## 📋 概要

Mac Status PWAに動画表示機能を統合しました。人物の顔部分以外をCSSマスクで隠す機能も含まれています。

## 📁 ファイル構造

```
frontend/
├── assets/
│   ├── videos/
│   │   ├── README.md              # 動画ファイル説明
│   │   ├── profile.mp4            # プロフィール動画（配置してください）
│   │   ├── demo.mp4               # デモ動画
│   │   └── thumbnails/            # サムネイル画像
│   ├── video-styles.css           # 動画表示用CSS
│   └── video-component.js         # 動画コンポーネント
└── fixed_index.html               # 更新されたメインHTML
```

## 🚀 セットアップ手順

### 1. 動画ファイルの配置

```bash
# 動画ファイルを配置
cp your-video.mp4 frontend/assets/videos/profile.mp4
```

**推奨仕様:**
- **形式**: MP4 (H.264コーデック)
- **解像度**: 1280x720 または 1920x1080
- **ファイルサイズ**: 10MB以下
- **長さ**: 10-30秒程度

### 2. サーバーの起動

```bash
python working_server.py
```

### 3. ブラウザでアクセス

```
http://localhost:8002/fixed
```

## 🎭 マスク機能

### 利用可能なマスクタイプ

1. **楕円マスク** (`oval`): 基本的な楕円形
2. **円形マスク** (`circle`): シンプルな円形
3. **人物マスク** (`portrait`): 人物の顔に最適化された楕円
4. **顔マスク** (`face`): より細長い楕円形
5. **カスタムマスク** (`custom`): 多角形の複雑な形状
6. **マスクなし** (`none`): マスクを適用しない

### マスクの調整

動画の右上にあるマスクセレクターで、リアルタイムでマスクタイプを変更できます。

## 💻 プログラムでの制御

### 基本的な使用方法

```javascript
// 新しい動画コンポーネントを作成
const videoComponent = new VideoComponent('containerId', {
    videoSrc: '/static/assets/videos/profile.mp4',
    maskType: 'portrait',
    size: 'medium',
    autoplay: true,
    loop: true,
    muted: true
});
```

### プリセット設定の使用

```javascript
// プロフィール用プリセット
const profileVideo = new VideoComponent('profileVideo', VideoPresets.profile);

// デモ用プリセット
const demoVideo = new VideoComponent('demoVideo', VideoPresets.demo);

// アバター用プリセット
const avatarVideo = new VideoComponent('avatarVideo', VideoPresets.avatar);
```

### 動的な制御

```javascript
// マスクタイプの変更
videoComponent.setMask('circle');

// 動画ソースの変更
videoComponent.setVideoSrc('/static/assets/videos/new-video.mp4');

// サイズの変更
videoComponent.setSize('large');

// 再生制御
videoComponent.play();
videoComponent.pause();
```

## 🎨 カスタマイズ

### CSSでのスタイル調整

```css
/* プロフィール動画のサイズ調整 */
.profile-video .video-container {
    width: 150px;
    height: 150px;
}

/* カスタムマスクの作成 */
.video-mask-heart {
    -webkit-clip-path: polygon(
        50% 0%, 
        61% 35%, 
        98% 35%, 
        68% 57%, 
        79% 91%, 
        50% 70%, 
        21% 91%, 
        32% 57%, 
        2% 35%, 
        39% 35%
    );
    clip-path: polygon(
        50% 0%, 
        61% 35%, 
        98% 35%, 
        68% 57%, 
        79% 91%, 
        50% 70%, 
        21% 91%, 
        32% 57%, 
        2% 35%, 
        39% 35%
    );
}
```

### 新しいマスクタイプの追加

```javascript
// video-component.jsのmaskTypesに追加
const maskTypes = [
    // 既存のマスク...
    { value: 'heart', label: 'ハート' },
    { value: 'star', label: '星' }
];
```

## 📱 レスポンシブ対応

動画コンポーネントは自動的にレスポンシブ対応されています：

- **デスクトップ**: フルサイズ表示
- **タブレット**: 中サイズ表示
- **モバイル**: 小サイズ表示

## 🔧 トラブルシューティング

### 動画が表示されない

1. **ファイルパスの確認**
   ```bash
   ls -la frontend/assets/videos/profile.mp4
   ```

2. **ブラウザコンソールでエラー確認**
   - F12 → Console タブ
   - エラーメッセージを確認

3. **動画形式の確認**
   - MP4形式であることを確認
   - H.264コーデックであることを確認

### マスクが適用されない

1. **ブラウザ対応の確認**
   - Chrome, Safari, Firefox の最新版を使用
   - `clip-path` プロパティがサポートされているか確認

2. **CSS読み込みの確認**
   ```html
   <link rel="stylesheet" href="/static/assets/video-styles.css">
   ```

### パフォーマンスの問題

1. **動画ファイルサイズの最適化**
   ```bash
   # FFmpegで圧縮
   ffmpeg -i input.mp4 -vcodec h264 -acodec mp2 output.mp4
   ```

2. **プリロードの無効化**
   ```javascript
   const videoComponent = new VideoComponent('containerId', {
       preload: 'none' // 必要時のみ読み込み
   });
   ```

## 🎯 使用例

### ヘッダーのプロフィール動画

```html
<div id="profileVideo" class="profile-video"></div>
```

```javascript
const profileVideo = initVideoComponent('profileVideo', 
    '/static/assets/videos/profile.mp4', 
    VideoPresets.profile
);
```

### チャット内のデモ動画

```html
<div id="demoVideo" class="demo-video"></div>
```

```javascript
const demoVideo = initVideoComponent('demoVideo', 
    '/static/assets/videos/demo.mp4', 
    VideoPresets.demo
);
```

## 📊 パフォーマンス最適化

### 推奨設定

```javascript
const optimizedSettings = {
    videoSrc: '/static/assets/videos/profile.mp4',
    maskType: 'portrait',
    size: 'medium',
    autoplay: true,
    loop: true,
    muted: true,        // 自動再生のため必須
    controls: false,    // カスタムコントロール使用
    preload: 'metadata' // メタデータのみプリロード
};
```

### メモリ使用量の監視

```javascript
// コンポーネントの破棄
videoComponent.destroy();

// メモリリークの防止
window.addEventListener('beforeunload', () => {
    if (profileVideoComponent) {
        profileVideoComponent.destroy();
    }
});
```

## 🔄 今後の拡張予定

1. **WebRTC対応**: リアルタイム動画ストリーミング
2. **動画エフェクト**: フィルターやエフェクトの追加
3. **音声認識**: 動画内の音声からテキスト生成
4. **AI分析**: 動画内容の自動分析と説明生成

---

**作成日**: 2025年8月1日  
**バージョン**: 1.0.0  
**対応ブラウザ**: Chrome 88+, Safari 14+, Firefox 78+