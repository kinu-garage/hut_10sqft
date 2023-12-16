; .emacs specific for 130s-p16s

; 2/8/2013 Ubuntu common setting ported
(load "~/link/ROS/130s/hut_10sqft/config/emacs/emacs_ubuntu.el")

; 4/6/2012/emacs tex live config
; 20170818 Comment out since this causes server error upon launch
;;(server-start)

;; Issue where texts are not shown with emacs -nw option is solved by using "when window-system"
;; https://www.emacswiki.org/emacs/FrameSize
;;(set-frame-height (selected-frame) 58)  ;; It seems important to disable set-frame-{height, width} when set-frame-size is in use.
;;(set-frame-width (selected-frame) 110)
(when window-system (set-frame-size (selected-frame) 100 70))
