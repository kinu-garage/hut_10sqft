; .emacs specific for tork-kudu1

; 2/8/2013 Ubuntu common setting ported
; 6/8/2016 Moved dir to the one in git repo.
(load "~/link/github_repos/130s/compenv_ubuntu/config/emacs/emacs_ubuntu_trusty.el")

;; Issue where texts are not shown with emacs -nw option is solved by using "when window-system"
;; https://www.emacswiki.org/emacs/FrameSize
;(set-frame-height (selected-frame) 48)
;(set-frame-width (selected-frame) 172)
(when window-system (set-frame-size (selected-frame) 188 52))
