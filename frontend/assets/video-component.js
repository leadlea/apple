/**
 * Video Component for Mac Status PWA
 * 動画表示とマスク機能のためのJavaScriptコンポーネント
 */

class VideoComponent {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            videoSrc: options.videoSrc || '',
            maskType: options.maskType || 'oval',
            size: options.size || 'medium',
            autoplay: options.autoplay || false,
            loop: options.loop || true,
            muted: options.muted || true,
            controls: options.controls || false,
            showMaskSelector: options.showMaskSelector || true,
            ...options
        };
        
        this.video = null;
        this.currentMask = this.options.maskType;
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('Video container not found');
            return;
        }
        
        this.createVideoElement();
        this.setupEventListeners();
        
        if (this.options.showMaskSelector) {
            this.createMaskSelector();
        }
    }
    
    createVideoElement() {
        // コンテナのHTML構造を作成
        this.container.innerHTML = `
            <div class="video-container ${this.options.size}">
                <video class="video-element video-mask-${this.currentMask}" 
                       ${this.options.autoplay ? 'autoplay' : ''}
                       ${this.options.loop ? 'loop' : ''}
                       ${this.options.muted ? 'muted' : ''}
                       ${this.options.controls ? 'controls' : ''}
                       playsinline>
                    <source src="${this.options.videoSrc}" type="video/mp4">
                    <p>お使いのブラウザは動画再生をサポートしていません。</p>
                </video>
                <div class="video-placeholder" style="display: none;">
                    動画を読み込み中...
                </div>
                <div class="video-controls" style="display: none;">
                    <button class="video-control-btn play-pause">⏸️</button>
                    <button class="video-control-btn volume">🔊</button>
                </div>
                <div class="mask-preview-overlay"></div>
            </div>
        `;
        
        this.video = this.container.querySelector('.video-element');
        this.placeholder = this.container.querySelector('.video-placeholder');
        this.controls = this.container.querySelector('.video-controls');
    }
    
    createMaskSelector() {
        const maskSelector = document.createElement('div');
        maskSelector.className = 'mask-selector';
        
        const maskTypes = [
            { value: 'oval', label: '楕円' },
            { value: 'circle', label: '円形' },
            { value: 'portrait', label: '人物' },
            { value: 'face', label: '顔' },
            { value: 'custom', label: 'カスタム' },
            { value: 'none', label: 'なし' }
        ];
        
        maskTypes.forEach(mask => {
            const button = document.createElement('button');
            button.className = `mask-option ${mask.value === this.currentMask ? 'active' : ''}`;
            button.textContent = mask.label;
            button.dataset.mask = mask.value;
            
            button.addEventListener('click', () => {
                this.changeMask(mask.value);
                this.updateMaskSelector(mask.value);
            });
            
            maskSelector.appendChild(button);
        });
        
        this.container.querySelector('.video-container').appendChild(maskSelector);
    }
    
    changeMask(maskType) {
        // 現在のマスククラスを削除
        this.video.className = this.video.className.replace(/video-mask-\w+/g, '');
        
        // 新しいマスククラスを追加
        if (maskType !== 'none') {
            this.video.classList.add(`video-mask-${maskType}`);
        }
        
        this.currentMask = maskType;
        
        // マスクプレビューを一時的に表示
        this.showMaskPreview();
    }
    
    updateMaskSelector(activeMask) {
        const options = this.container.querySelectorAll('.mask-option');
        options.forEach(option => {
            option.classList.toggle('active', option.dataset.mask === activeMask);
        });
    }
    
    showMaskPreview() {
        const container = this.container.querySelector('.video-container');
        container.classList.add('show-mask-preview');
        
        setTimeout(() => {
            container.classList.remove('show-mask-preview');
        }, 1000);
    }
    
    setupEventListeners() {
        // 動画の読み込み状態を監視
        this.video.addEventListener('loadstart', () => {
            this.placeholder.style.display = 'flex';
        });
        
        this.video.addEventListener('canplay', () => {
            this.placeholder.style.display = 'none';
        });
        
        this.video.addEventListener('error', (e) => {
            console.error('Video loading error:', e);
            this.placeholder.innerHTML = '動画の読み込みに失敗しました';
        });
        
        // カスタムコントロール
        if (!this.options.controls) {
            this.setupCustomControls();
        }
    }
    
    setupCustomControls() {
        const playPauseBtn = this.container.querySelector('.play-pause');
        const volumeBtn = this.container.querySelector('.volume');
        
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => {
                if (this.video.paused) {
                    this.video.play();
                    playPauseBtn.textContent = '⏸️';
                } else {
                    this.video.pause();
                    playPauseBtn.textContent = '▶️';
                }
            });
        }
        
        if (volumeBtn) {
            volumeBtn.addEventListener('click', () => {
                this.video.muted = !this.video.muted;
                volumeBtn.textContent = this.video.muted ? '🔇' : '🔊';
            });
        }
        
        // ホバー時にコントロールを表示
        const container = this.container.querySelector('.video-container');
        container.addEventListener('mouseenter', () => {
            if (!this.options.controls) {
                this.controls.style.display = 'flex';
            }
        });
        
        container.addEventListener('mouseleave', () => {
            if (!this.options.controls) {
                this.controls.style.display = 'none';
            }
        });
    }
    
    // パブリックメソッド
    play() {
        return this.video.play();
    }
    
    pause() {
        this.video.pause();
    }
    
    setVideoSrc(src) {
        this.video.src = src;
        this.options.videoSrc = src;
    }
    
    setMask(maskType) {
        this.changeMask(maskType);
        this.updateMaskSelector(maskType);
    }
    
    setSize(size) {
        const container = this.container.querySelector('.video-container');
        container.className = container.className.replace(/video-\w+/g, '');
        container.classList.add(`video-${size}`);
        this.options.size = size;
    }
    
    destroy() {
        if (this.video) {
            this.video.pause();
            this.video.src = '';
        }
        this.container.innerHTML = '';
    }
}

// 使用例とヘルパー関数
window.VideoComponent = VideoComponent;

// 簡単な初期化ヘルパー
window.initVideoComponent = function(containerId, videoSrc, options = {}) {
    return new VideoComponent(containerId, {
        videoSrc: videoSrc,
        ...options
    });
};

// 複数の動画を一括初期化
window.initMultipleVideos = function(configs) {
    const components = [];
    
    configs.forEach(config => {
        const component = new VideoComponent(config.containerId, config.options);
        components.push(component);
    });
    
    return components;
};

// プリセット設定
window.VideoPresets = {
    profile: {
        maskType: 'portrait',
        size: 'medium',
        autoplay: true,
        loop: true,
        muted: true,
        controls: false,
        showMaskSelector: true
    },
    
    demo: {
        maskType: 'none',
        size: 'large',
        autoplay: false,
        loop: false,
        muted: false,
        controls: true,
        showMaskSelector: false
    },
    
    avatar: {
        maskType: 'circle',
        size: 'small',
        autoplay: true,
        loop: true,
        muted: true,
        controls: false,
        showMaskSelector: false
    }
};