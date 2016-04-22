;;; 言語環境の指定
;;mozcの設定
;;;(require 'mozc)
;;;(set-language-environment "Japanese")
;;;(setq default-input-method "japanese-mozc")

;;ドル記号を入力したときに直接入力に切り替える。
;;;(define-key mozc-mode-map "$" 'YaTeX-insert-dollar-or-mozc-insert)
;;;(define-key mozc-mode-map "\C-\o" 'YaTeX-insert-dollar-or-mozc-insert)
;;;(defun YaTeX-insert-dollar-or-mozc-insert ()
;;;  (interactive)
;;;  (if (eq major-mode 'yatex-mode)
;;;      (YaTeX-insert-dollar)
;;;    (mozc-insert)))
