;; 6/9/2016 Common config read here.
(load "~/.config/hut_10sqft/hut_10sqft/config/emacs/debian.el")

; 6/30/2012/http://superuser.com/questions/165278/copying-text-from-emacs-into-other-programs
(setq x-select-enable-clipboard t)      ;Make kill/yank work with the X clipboard
(setq interprogram-paste-function 'x-cut-buffer-or-selection-value)

; 2021/11/30 ; roslaunch highlighting http://wiki.ros.org/roslaunch/Tutorials/Using%20Roslaunch%20with%20Emacs
(add-to-list 'auto-mode-alist '("\\.launch$" . xml-mode))
(add-to-list 'auto-mode-alist '("\\.test$" . xml-mode))

; 2/19/2012/ SLIME (IDE for Lisp)
; http://www.cliki.net/SLIME-HOWTO
;;(add-to-list 'load-path "/usr/share/emacs23/site-lisp/slime")
;;(require 'slime)
;;(add-hook 'lisp-mode-hook (lambda () (slime-mode t)))
;;(add-hook 'inferior-lisp-mode-hook (lambda () (inferior-slime-mode t)))
;; Optionally, specify the lisp program you are using. Default is "lisp"
;;(setq inferior-lisp-program "clisp") 

; Mew + Gmail
; http://jedipunkz.github.io/blog/2013/08/12/emacs-mew-gmail/
(autoload 'mew "mew" nil t)
(autoload 'mew-send "mew" nil t)
(setq mew-fcc "+outbox") ; Save sent mails
(setq exec-path (cons "/usr/bin" exec-path))
(put 'upcase-region 'disabled nil)

;; Creating short cut
(set-register ?d '(file . "~/data/Dropbox/periodic/2024/"))
(set-register ?s '(file . "~/data/Dropbox/app/Synergy/"))
