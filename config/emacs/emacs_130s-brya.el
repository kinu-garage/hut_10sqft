; .emacs specific for 130s-brya ChromeOS
; 20231123 Originally copied from emacs_130s-p16s.el

(load "~/link/ROS/130s/hut_10sqft/config/emacs/emacs.el")

;; Issue where texts are not shown with emacs -nw option is solved by using "when window-system"
;; https://www.emacswiki.org/emacs/FrameSize
;;(set-frame-height (selected-frame) 58)  ;; It seems important to disable set-frame-{height, width} when set-frame-size is in use.
;;(set-frame-width (selected-frame) 110)
(when window-system (set-frame-size (selected-frame) 88 34))
