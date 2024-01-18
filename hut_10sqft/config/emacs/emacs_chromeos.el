; .emacs specific for 130s-brya ChromeOS
; 20231123 Originally copied from emacs_130s-p16s.el

(load "~/.config/hut_10sqft/hut_10sqft/config/emacs/emacs.el")

;; Creating short cut
(set-register ?d '(file . "~/link/Current/"))

;; Emacs GUI default size
;; Determined by 130s-brya (13inch, 1920x1680). Can be re-defined in downstream if desired.
(when window-system (set-frame-size (selected-frame) 88 34))

;; Toggling OS language choice
;;
;; The following, which is taken from an Emacs config on Linux, doesn't seem to work (likely because `toggle-input-method` doesn't work on ChromeOS?).
; (global-set-key (kbd "\C-q") 'toggle-input-method)

;;20240117 Copied from ./emacs_ubuntu.el and modified hoping this works on ChromeOS. See https://github.com/kinu-garage/hut_10sqft/issues/983
;; mozc
(require 'mozc)
; 2/15/2016 Without this, encoding may not be saved proerply?
(set-language-environment "Japanese")
(setq default-input-method "japanese-mozc")
;;;(global-set-key (kbd "\C-o") 'toggle-input-method)  ; This doesn't seem to be working. Probably collides with OS' input key that is also \C-o ?
(global-set-key (kbd "\C-q") 'toggle-input-method)
; 20160609 Not sure how effective this is but I just leave it. https://wiki.archlinuxjp.org/index.php/Mozc#Emacs_.E3.81.A7_Mozc_.E3.82.92.E4.BD.BF.E3.81.86
(setq mozc-candidate-style 'overlay)
