;; 6/9/2016 Common config read here.
(load "~/link/ROS/src/130s/hut_10sqft/config/emacs/emacs.el")

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

; 2019/05/15 Macro to convert fragmented merge requests link to a full valid http URL for Gitlab.com.
(fset 'strreplace_mr_gitlab
   (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ("see merge request phttps://!/merge_requests/" 0 "%d")) arg)))

; 2019/10/09 Macro to convert a Gitlab http URL of an issue on any POR repo to link format in .md.
; e.g. https://gitlab.com/remote-org/git-group/sub-group/issues/473 -> [git-group/sub-group#473](https://gitlab.com/remote-org/git-group/sub-group/issues/473)
(fset 'strreplace_url_por_md
   (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ([19 104 116 116 112 115 6 19 105 115 115 117 101 115 134217830 67108896 18 104 116 116 112 115 2 6 23 25 41 18 104 116 116 112 115 2 6 91 25 93 40 18 91 6 67108896 19 112 108 117 115 111 110 101 45 114 111 98 111 116 105 99 115 6 23 19 105 115 115 117 101 6 6 127 127 127 127 127 127 127 127 35 19 41 6 27 120 107 109 97 99 114 111 45 101 tab 110 100 tab 111 114 tab] 0 "%d")) arg)))

; 2019/10/09 Macro to convert a Gitlab http URL of an issue on any POR repo to link format in .rst.
; e.g. https://gitlab.com/remote-org/git-group/sub-group/issues/999 -> `git-group/sub-group#999 <https://gitlab.com/remote-org/git-group/sub-group/issues/999>`_
(fset 'strreplace_url_por_rst
   (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ([19 104 116 116 112 115 6 2 2 2 2 2 2 67108896 19 105 115 115 117 101 134217830 134217830 23 25 62 96 95 18 104 116 116 112 115 6 2 96 25 32 60 18 104 116 116 6 4 127 67108896 19 112 108 117 115 111 110 101 45 114 111 98 111 116 105 99 115 6 23 19 105 115 115 4 4 4 4 127 127 127 127 35 19 62 96 6 27 120 107 109 97 tab 101 110 100 tab 111 tab] 0 "%d")) arg)))

; 2021/11/30 ; roslaunch highlighting http://wiki.ros.org/roslaunch/Tutorials/Using%20Roslaunch%20with%20Emacs
(add-to-list 'auto-mode-alist '("\\.launch$" . xml-mode))
(add-to-list 'auto-mode-alist '("\\.test$" . xml-mode))
