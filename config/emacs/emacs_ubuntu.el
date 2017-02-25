;; 6/9/2016 Common config read here.
(load "~/link/github_repos/130s/hut_10sqft/config/emacs/emacs.el")

;;20160429 Moved from downstream (kudu1, Trusty 14.04), hoping this is valid for all Ubuntu machines.
;; mozc
(require 'mozc)
; 2/15/2016 Without this, encoding may not be saved proerply?
(set-language-environment "Japanese")
(setq default-input-method "japanese-mozc")
;;;(global-set-key (kbd "\C-o") 'toggle-input-method)  ; This doesn't seem to be working. Probably collides with OS' input key that is also \C-o ?
(global-set-key (kbd "\C-q") 'toggle-input-method)
; 20160609 Not sure how effective this is but I just leave it. https://wiki.archlinuxjp.org/index.php/Mozc#Emacs_.E3.81.A7_Mozc_.E3.82.92.E4.BD.BF.E3.81.86
(setq mozc-candidate-style 'overlay)

; 6/30/2012/http://superuser.com/questions/165278/copying-text-from-emacs-into-other-programs
(setq x-select-enable-clipboard t)      ;Make kill/yank work with the X clipboard
(setq interprogram-paste-function 'x-cut-buffer-or-selection-value)
