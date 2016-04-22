; .emacs specific for tork-kudu1

; 2/8/2013 Ubuntu common setting ported
(load "./emacs_ubuntu.el")
(load "./emacs_ubuntu_trusty.el")

;; mozc
(require 'mozc)
(setq default-input-method "japanese-mozc")

;;ドル記号を入力したときに直接入力に切り替える。
;;;(define-key mozc-mode-map "$" 'YaTeX-insert-dollar-or-mozc-insert)
(define-key mozc-mode-map "\C-\o" 'YaTeX-insert-dollar-or-mozc-insert)
(defun YaTeX-insert-dollar-or-mozc-insert ()
  (interactive)
  (if (eq major-mode 'yatex-mode)
      (YaTeX-insert-dollar)
    (mozc-insert)))

;; Issue where texts are not shown with emacs -nw option is solved by using "when window-system"
;; https://www.emacswiki.org/emacs/FrameSize
;(set-frame-height (selected-frame) 48)
;(set-frame-width (selected-frame) 172)
(when window-system (set-frame-size (selected-frame) 172 58))
