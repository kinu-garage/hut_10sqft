; .emacs specific for 130s-serval

; 2/8/2013 Ubuntu common setting ported
(load "~/data/Dropbox/app/bash/compenv_ubuntu/config/emacs/emacs_ubuntu.el")
(load "~/data/Dropbox/app/bash/compenv_ubuntu/config/emacs/emacs_ubuntu_precise.el")

(set-frame-height (selected-frame) 44)
(set-frame-width (selected-frame) 90)

; Mew + Gmail
; http://jedipunkz.github.io/blog/2013/08/12/emacs-mew-gmail/
(autoload 'mew "mew" nil t)
(autoload 'mew-send "mew" nil t)
(setq mew-fcc "+outbox") ; Save sent mails
(setq exec-path (cons "/usr/bin" exec-path))
