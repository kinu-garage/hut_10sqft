;from cns.sfc/2005/sep/27
; Coloring window
(cond
 ((and window-system (string-match "^19" emacs-version))
  (require 'hilit19)))

(setq mh-letter-mode-hook
      (function
         (lambda ()
(setq mh-ins-buf-prefix ">")
(setq mh-yank-from-start-of-msg 'body)
(turn-on-auto-fill))))

;;; Launch lisp
;;
;;  NL1
;;

;(setq inferior-lisp-program "gcl")
;
;(setq default-kanji-process-code 3)
;
;(defun save-buffer-euc ()
;  (interactive)
;  (let ((lisp-mode "lisp-mode")
;	(mode major-mode))
;    (if (string= mode lisp-mode)
;	(progn (setq kanji-fileio-code 3)
;	       (save-buffer)
;	       (message "Save buffer in EUC.")
;	       (setq kanji-fileio-code 1)
;	       (change-fileio-code)))))

;(define-key lisp-mode-map "\C-x\C-s" 'save-buffer-euc)

;(setq auto-mode-alist (cons '("\\.dic$" . lisp-mode)
;			    (cons '("\\.grm$" . lisp-mode) auto-mode-alist)))

;for GCL use
;(setq inferior-lisp-program "gcl")

;;Swap \C-h on delete-backward-char
;(load-library "term/keyswap")
;(if (eq window-system 'x)
;    (progn
;      (define-keyfunction-key-map [delete] [8])
;      (put 'delete 'ascii-character 8)))
(keyboard-translate ?\C-h ?\C-?)
(global-set-key "\C-h" nil)

;ime/2005/oct/15
;(global-set-key "\C-o" 'mw32-ime-toggle)

;2005/nov/10/setting color
;http://home.att.ne.jp/alpha/z123/elisp-j.html
(if window-system (progn

  ;; text color
  (set-foreground-color "aquamarine")
  ;; background color
  (set-background-color "DarkGreen")
;;;  (set-background-color "gold4")
;;;  (set-background-color "DarkSlateGrey")
;;;  (set-background-color "SlateBlue")
  ;; mode line color
  ;(set-face-foreground 'modeline "white") ;3/8/14 Seems invalid on win8?
  ;; mode line background color
  ;(set-face-background 'modeline "MediumPurple2") ;3/8/14 Seems invalid on win8?
  ;; cursor color
  (set-cursor-color "MediumPurple2")
  ;; mouse pointer color
  (set-mouse-color  "MediumPurple2")
))

;; For folding a line by specified number of characters
(add-hook 'text-mode-hook
          '(lambda ()
             (setq fill-column 78)
;             (auto-fill-mode 1)
             ))

; window size upon boot
; 10/23/2012 delegated to each machine's setting file.
;;(set-frame-height (selected-frame) 44)
;;(set-frame-width (selected-frame) 94)

;; 5/31/2011 Word Count.   ONLY for Mac???
;; http://blog.lilyx.net/2007/10/02/emacs-word-count-mode/
;(setq load-path (cons (expand-file-name "/Applications/Emacs_Carbon/") load-path))
(autoload 'word-count-mode "word-count"
          "Minor mode to count words." t nil)
(global-set-key "\M-+" 'word-count-mode)

; 3/15/2012/For ignoring cases. As of today these are not in effect.
(setq completion-ignore-case t)
(setq read-buffer-completion-ignore-case t)

; 4/1/2012/ROS setting is exported
;;(load "~/ROS_Workspace/Shared_MultiHosts_ROS_Workspace/.emacs_ros") ; 7/3/2012/This is now referred from ~/.emacs

;; 10/30/2015 http://superuser.com/questions/255475/emacs-setting-column-mode-to-be-always-on
(setq column-number-mode t)

;; 20160708 auto complete missing xml tag
;; http://superuser.com/questions/383520/how-to-efficiently-type-in-a-pair-of-xml-tags-in-emacs
;; associate xml, xsd, etc with nxml-mode
(add-to-list 'auto-mode-alist (cons (concat "\\." (regexp-opt '("xml" "xsd" "rng" "xslt" "xsl") t) "\\'") 'nxml-mode))
(setq nxml-slash-auto-complete-flag t)

;; 20160708 Fold xml elements by `C-c h` 
;; http://emacs.stackexchange.com/questions/2884/the-old-how-to-fold-xml-question?newreg=e088fec681974846a759fffd1a4aa693
(require 'hideshow)
(require 'sgml-mode)
(require 'nxml-mode)
(add-to-list 'hs-special-modes-alist
             '(nxml-mode
               "<!--\\|<[^/>]*[^/]>"
               "-->\\|</[^/>]*[^/]>"

               "<!--"
               sgml-skip-tag-forward
               nil))
(add-hook 'nxml-mode-hook 'hs-minor-mode)

;; optional key bindings, easier than hs defaults
(define-key nxml-mode-map (kbd "C-c h") 'hs-toggle-hiding)

;; 20201203 Frame https://emacs.stackexchange.com/questions/5371/how-to-change-emacs-windows-from-vertical-split-to-horizontal-split
(setq load-path (cons (expand-file-name "~/.config/hut_10sqft/hut_10sqft/config/emacs/3rd_party_emacs/") load-path))
(require 'transpose-frame)

; 2019/05/15 Macro to convert fragmented merge requests link to a full valid http URL for Gitlab.com.
(fset 'strreplace_mr_gitlab
   (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ("see merge request phttps://!/merge_requests/" 0 "%d")) arg)))

; 2019/10/09 Macro to convert a Gitlab http URL of an issue on any POR repo to link format in .md.
; e.g. https://gitlab.com/remote-org/git-group/sub-group/issues/473 -> [git-group/sub-group#473](https://gitlab.com/remote-org/git-group/sub-group/issues/473)
(fset 'strreplace_url_por_md
   (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ([19 104 116 116 112 115 6 19 105 115 115 117 101 115 134217830 67108896 18 104 116 116 112 115 2 6 23 25 41 18 104 116 116 112 115 2 6 91 25 93 40 18 91 6 67108896 19 112 108 117 115 111 110 101 45 114 111 98 111 116 105 99 115 6 23 19 105 115 115 117 101 6 6 127 127 127 127 127 127 127 127 35 19 41 6 27 120 107 109 97 99 114 111 45 101 tab 110 100 tab 111 114 tab] 0 "%d")) arg)))

; 2019/10/09 Macro to convert a Gitlab http URL of an issue on any POR repo to link format in .rst.
; e.g. https://gitlab.com/remote-org/git-group/sub-group/issues/999 -> `git-group/sub-group#999 <https://gitlab.com/remote-org/git-group/sub-group/issues/999>`_
(fset 'strreplace_url_por_rst
   (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ([19 104 116 116 112 115 6 2 2 2 2 2 2 67108896 19 105 115 115 117 101 134217830 134217830 23 25 62 96 95 18 104 116 116 112 115 6 2 96 25 32 60 18 104 116 116 6 4 127 67108896 19 112 108 117 115 111 110 101 45 114 111 98 111 116 105 99 115 6 23 19 105 115 115 4 4 4 4 127 127 127 127 35 19 62 96 6 27 120 107 109 97 tab 101 110 100 tab 111 tab] 0 "%d")) arg)))

; 4/6/2012/emacs tex live config
(server-start)
