; .emacs specific for 130s-brya ChromeOS
; 20231123 Originally copied from emacs_130s-p16s.el

(load "~/.config/hut_10sqft/hut_10sqft/config/emacs/debian.el")

;; Creating short cut
(set-register ?d '(file . "~/link/Current/"))

;; Emacs GUI default size
;; Determined by 130s-brya (13inch, 1920x1680). Can be re-defined in downstream if desired.
(when window-system (set-frame-size (selected-frame) 88 34))
