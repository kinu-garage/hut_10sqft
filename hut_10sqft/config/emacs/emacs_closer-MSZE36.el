; .emacs specific for closer-MSZE36.el (originally based off of 130s-p16s)

;; Load setup for a dev Ubuntu host.
(load "~/.config/hut_10sqft/hut_10sqft/config/emacs/emacs_130s-p16s.el")

;; 20260325 debug https://github.com/kinu-garage/hut_10sqft/issues/1411 suggested by Gemini
(tooltip-mode -1)
(setq use-gtk-tooltip nil)
