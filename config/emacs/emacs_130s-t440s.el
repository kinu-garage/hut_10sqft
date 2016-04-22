; .emacs specific for 130s-t440s (Ubuntu Trusty)

; 2/8/2013 Ubuntu common setting ported
(load "~/data/Dropbox/app/bash/compenv_ubuntu/config/emacs/emacs_ubuntu.el")
(load "~/data/Dropbox/app/bash/compenv_ubuntu/config/emacs/emacs_ubuntu_trusty.el")

; 4/6/2012/emacs tex live config
(server-start)

; 2/17/2012/To enabele run-lisp
; http://www.cs.berkeley.edu/~russell/classes/cs188/f05/assignments/a0/lisp-tutorial.html
(setq inferior-lisp-program "/usr/bin/clisp")
(global-set-key "\C-x\C-l" `run-lisp)
(global-set-key "\C-xd" `lisp-eval-defun)
(global-set-key "\C-x\C-d" `lisp-eval-defun-and-go)  

(set-frame-height (selected-frame) 50)
(set-frame-width (selected-frame) 184)

; Mew + Gmail
; http://jedipunkz.github.io/blog/2013/08/12/emacs-mew-gmail/
(autoload 'mew "mew" nil t)
(autoload 'mew-send "mew" nil t)
(setq mew-fcc "+outbox") ; Save sent mails
(setq exec-path (cons "/usr/bin" exec-path))

