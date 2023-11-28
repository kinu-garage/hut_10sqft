;; 6/9/2016 Common config read here.
(load "~/link/ROS/130s/hut_10sqft/config/emacs/emacs.el")

;; Issue where texts are not shown with emacs -nw option is solved by using "when window-system"
;; https://www.emacswiki.org/emacs/FrameSize
(when window-system (set-frame-size (selected-frame) 94 20))

;; 3/24/2013 To enable pdflatex http://emacswiki.org/emacs/AUCTeX
(setq TeX-PDF-mode t)
