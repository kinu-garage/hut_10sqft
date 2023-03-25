; .emacs specific for 130s-kudu1

; 2/8/2013 Ubuntu common setting ported
(load "~/link/ROS/src/130s/hut_10sqft/config/emacs/emacs_ubuntu.el")
(load "~/link/ROS/src/130s/hut_10sqft/config/emacs/emacs_ubuntu_trusty.el")

;; mozc
(require 'mozc)
(set-language-environment "Japanese")
(setq default-input-method "japanese-mozc")
;;;
;;ドル記号を入力したときに直接入力に切り替える。
;;;(define-key mozc-mode-map "$" 'YaTeX-insert-dollar-or-mozc-insert)
(define-key mozc-mode-map "\C-\o" 'YaTeX-insert-dollar-or-mozc-insert)
(defun YaTeX-insert-dollar-or-mozc-insert ()
  (interactive)
  (if (eq major-mode 'yatex-mode)
      (YaTeX-insert-dollar)
    (mozc-insert)))

(set-frame-height (selected-frame) 48)
(set-frame-width (selected-frame) 172)
