; .emacs specific for 130s-serval

; 2/8/2013 Ubuntu common setting ported
(load "~/data/Dropbox/app/bash/compenv_ubuntu/config/emacs/emacs_ubuntu.el")

; 4/6/2012/emacs tex live config
(server-start)

; 2/17/2012/To enabele run-lisp
; http://www.cs.berkeley.edu/~russell/classes/cs188/f05/assignments/a0/lisp-tutorial.html
(setq inferior-lisp-program "/usr/bin/clisp")
(global-set-key "\C-x\C-l" `run-lisp)
(global-set-key "\C-xd" `lisp-eval-defun)
(global-set-key "\C-x\C-d" `lisp-eval-defun-and-go)  

; 2/19/2012/ SLIME (IDE for Lisp)
; http://www.cliki.net/SLIME-HOWTO
;;(add-to-list 'load-path "/usr/share/emacs23/site-lisp/slime")
;;(require 'slime)
;;(add-hook 'lisp-mode-hook (lambda () (slime-mode t)))
;;(add-hook 'inferior-lisp-mode-hook (lambda () (inferior-slime-mode t)))
;; Optionally, specify the lisp program you are using. Default is "lisp"
;;(setq inferior-lisp-program "clisp") 

;; Issue where texts are not shown with emacs -nw option is solved by using "when window-system"
;; https://www.emacswiki.org/emacs/FrameSize
(set-frame-height (selected-frame) 58)
(set-frame-width (selected-frame) 110)
(when window-system (set-frame-size (selected-frame) 152 58))

; Mew + Gmail
; http://jedipunkz.github.io/blog/2013/08/12/emacs-mew-gmail/
(autoload 'mew "mew" nil t)
(autoload 'mew-send "mew" nil t)
(setq mew-fcc "+outbox") ; Save sent mails
(setq exec-path (cons "/usr/bin" exec-path))
