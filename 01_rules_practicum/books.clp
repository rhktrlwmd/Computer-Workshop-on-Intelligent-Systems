; Сгенерировано из knowledge.py командой python framework.py

(deftemplate known (slot value (type STRING)))

(deftemplate fired (slot rule (type STRING)) (slot added (type STRING)))

(deftemplate selected (slot book (type STRING)) (slot reason (type STRING)))

(defrule R01
  (declare (salience 1000))
  (known (value "likes_science"))
  (not (known (value "genre_sf")))
  =>
  (assert (known (value "genre_sf")))
  (assert (fired (rule "R01") (added "genre_sf"))))

(defrule R02
  (declare (salience 999))
  (known (value "likes_mystery"))
  (not (known (value "genre_detective")))
  =>
  (assert (known (value "genre_detective")))
  (assert (fired (rule "R02") (added "genre_detective"))))

(defrule R03
  (declare (salience 998))
  (known (value "likes_magic"))
  (not (known (value "genre_fantasy")))
  =>
  (assert (known (value "genre_fantasy")))
  (assert (fired (rule "R03") (added "genre_fantasy"))))

(defrule R09
  (declare (salience 997))
  (known (value "genre_detective"))
  (known (value "prefers_short"))
  (known (value "prefers_classics"))
  (not (known (value "candidate:sherlock")))
  =>
  (assert (known (value "candidate:sherlock")))
  (assert (fired (rule "R09") (added "candidate:sherlock"))))

(defrule select-R09
  (declare (salience -1003))
  (known (value "genre_detective"))
  (known (value "prefers_short"))
  (known (value "prefers_classics"))
  (known (value "candidate:sherlock"))
  (not (selected))
  =>
  (assert (selected (book "sherlock") (reason "R09"))))

(defrule R05
  (declare (salience 996))
  (known (value "genre_sf"))
  (known (value "likes_adventure"))
  (not (known (value "candidate:martian")))
  =>
  (assert (known (value "candidate:martian")))
  (assert (fired (rule "R05") (added "candidate:martian"))))

(defrule select-R05
  (declare (salience -1004))
  (known (value "genre_sf"))
  (known (value "likes_adventure"))
  (known (value "candidate:martian"))
  (not (selected))
  =>
  (assert (selected (book "martian") (reason "R05"))))

(defrule R06
  (declare (salience 995))
  (known (value "genre_sf"))
  (known (value "likes_philosophy"))
  (not (known (value "candidate:solaris")))
  =>
  (assert (known (value "candidate:solaris")))
  (assert (fired (rule "R06") (added "candidate:solaris"))))

(defrule select-R06
  (declare (salience -1005))
  (known (value "genre_sf"))
  (known (value "likes_philosophy"))
  (known (value "candidate:solaris"))
  (not (selected))
  =>
  (assert (selected (book "solaris") (reason "R06"))))

(defrule R08
  (declare (salience 994))
  (known (value "genre_detective"))
  (known (value "prefers_short"))
  (not (known (value "candidate:sherlock")))
  =>
  (assert (known (value "candidate:sherlock")))
  (assert (fired (rule "R08") (added "candidate:sherlock"))))

(defrule select-R08
  (declare (salience -1006))
  (known (value "genre_detective"))
  (known (value "prefers_short"))
  (known (value "candidate:sherlock"))
  (not (selected))
  =>
  (assert (selected (book "sherlock") (reason "R08"))))

(defrule R11
  (declare (salience 993))
  (known (value "genre_fantasy"))
  (known (value "likes_adventure"))
  (not (known (value "candidate:hobbit")))
  =>
  (assert (known (value "candidate:hobbit")))
  (assert (fired (rule "R11") (added "candidate:hobbit"))))

(defrule select-R11
  (declare (salience -1007))
  (known (value "genre_fantasy"))
  (known (value "likes_adventure"))
  (known (value "candidate:hobbit"))
  (not (selected))
  =>
  (assert (selected (book "hobbit") (reason "R11"))))

(defrule R12
  (declare (salience 992))
  (known (value "genre_fantasy"))
  (known (value "likes_philosophy"))
  (not (known (value "candidate:earthsea")))
  =>
  (assert (known (value "candidate:earthsea")))
  (assert (fired (rule "R12") (added "candidate:earthsea"))))

(defrule select-R12
  (declare (salience -1008))
  (known (value "genre_fantasy"))
  (known (value "likes_philosophy"))
  (known (value "candidate:earthsea"))
  (not (selected))
  =>
  (assert (selected (book "earthsea") (reason "R12"))))

(defrule R04
  (declare (salience 991))
  (known (value "genre_sf"))
  (not (known (value "candidate:solaris")))
  =>
  (assert (known (value "candidate:solaris")))
  (assert (fired (rule "R04") (added "candidate:solaris"))))

(defrule select-R04
  (declare (salience -1009))
  (known (value "genre_sf"))
  (known (value "candidate:solaris"))
  (not (selected))
  =>
  (assert (selected (book "solaris") (reason "R04"))))

(defrule R07
  (declare (salience 990))
  (known (value "genre_detective"))
  (not (known (value "candidate:orient_express")))
  =>
  (assert (known (value "candidate:orient_express")))
  (assert (fired (rule "R07") (added "candidate:orient_express"))))

(defrule select-R07
  (declare (salience -1010))
  (known (value "genre_detective"))
  (known (value "candidate:orient_express"))
  (not (selected))
  =>
  (assert (selected (book "orient_express") (reason "R07"))))

(defrule R10
  (declare (salience 989))
  (known (value "genre_fantasy"))
  (not (known (value "candidate:earthsea")))
  =>
  (assert (known (value "candidate:earthsea")))
  (assert (fired (rule "R10") (added "candidate:earthsea"))))

(defrule select-R10
  (declare (salience -1011))
  (known (value "genre_fantasy"))
  (known (value "candidate:earthsea"))
  (not (selected))
  =>
  (assert (selected (book "earthsea") (reason "R10"))))
