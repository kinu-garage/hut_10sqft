(setq inferior-lisp-program "gcl")

(setq default-kanji-process-code 3)

(defun save-buffer-euc ()
  (interactive)
  (let ((lisp-mode "lisp-mode")
	(mode major-mode))
    (if (string= mode lisp-mode)
	(progn (setq kanji-fileio-code 3)
	       (save-buffer)
	       (message "Save buffer in EUC.")
	       (setq kanji-fileio-code 1)
	       (change-fileio-code)))))

(define-key lisp-mode-map "\C-x\C-s" 'save-buffer-euc)

(setq auto-mode-alist (cons '("\\.dic$" . lisp-mode)
			    (cons '("\\.grm$" . lisp-mode) auto-mode-alist)))
;for GCL use
(setq inferior-lisp-program "gcl")

;ime/2005/oct/15
(global-set-key "\C-o" 'mw32-ime-toggle)

;2005/nov/10/setting color
;http://home.att.ne.jp/alpha/z123/elisp-j.html
(if window-system (progn

  ;; 文字の色を設定します。
  (set-foreground-color "aquamarine")
  ;; 背景色を設定します。
  (set-background-color "DarkGreen")
;;;  (set-background-color "gold4")
;;;  (set-background-color "DarkSlateGrey")
;;;  (set-background-color "SlateBlue")
  ;; モードラインの文字の色を設定します。
  (set-face-foreground 'modeline "white")
  ;; モードラインの背景色を設定します。
  (set-face-background 'modeline "MediumPurple2")
  ;; カーソルの色を設定します。
  (set-cursor-color "MediumPurple2")
  ;; マウスポインタの色を設定します。
  (set-mouse-color  "MediumPurple2")

))

;; === Fix the "copy-paste from MS Word" issue on Mac OS X ===
;; prohibit pasting as TIFFs
(defun x-selection-value (type)
 (let ((data-types '(public.file-url
                      public.utf16-plain-text
                      com.apple.traditional-mac-plain-text))
   text)
   (while (and (null text) data-types)
     (setq text (condition-case nil
            (x-get-selection type (car data-types))
          (error nil)))
     (setq data-types (cdr data-types)))
   (if text
   (remove-text-properties 0 (length text) '(foreign-selection nil)
text))
   text))

; 2/8/2011 AUCTex aware of style files and multi-file documents right away
     (setq TeX-auto-save t)
     (setq TeX-parse-self t)
     (setq-default TeX-master nil)

;; 5/31/2011 Word Count
;; http://blog.lilyx.net/2007/10/02/emacs-word-count-mode/
(setq load-path (cons (expand-file-name "/Applications/Emacs_Carbon/") load-path))

;; 4/15/2013 Latex
;; Ref. http://superuser.com/a/285078/106974
(setenv "PATH" (concat "/usr/texbin:/usr/local/bin:" (getenv "PATH")))
(setq exec-path (append '("/usr/texbin" "/usr/local/bin") exec-path))
(load "auctex.el" nil t t)
(load "preview-latex.el" nil t t)
