; Обратный поиск реализован на языке CLIPS через рекурсивную deffunction.
; Здесь используются только исходные bc-known: прямой вывод не запускается.
(deftemplate bc-known (slot value (type STRING)))
(deftemplate bc-rule
  (slot rank (type INTEGER))
  (slot name (type STRING))
  (slot conclusion (type STRING))
  (multislot conditions (type STRING)))
(deftemplate bc-proof
  (slot goal (type STRING))
  (slot rule (type STRING) (default ""))
  (multislot children (type INTEGER)))
(deftemplate bc-event
  (slot depth (type INTEGER))
  (slot message (type STRING)))

; Результат: индекс факта bc-proof при успехе, 0 при неудаче.
(deffunction prove-goal (?goal $?path)
  (bind ?depth (length$ ?path))
  (assert (bc-event (depth ?depth) (message (str-cat "Проверяем " ?goal))))
  (if (any-factp ((?fact bc-known)) (eq ?fact:value ?goal)) then
    (assert (bc-event (depth ?depth) (message "Есть в исходных фактах")))
    (return (fact-index (assert (bc-proof (goal ?goal))))))
  (if (member$ ?goal ?path) then
    (assert (bc-event (depth ?depth) (message "Цикл в текущей ветви")))
    (return 0))

  ; rank задаёт тот же порядок альтернатив, что ordered() в Python.
  (bind ?count (length$ (find-all-facts ((?r bc-rule)) TRUE)))
  (loop-for-count (?rank 0 (- ?count 1))
    (bind ?matches (find-fact ((?r bc-rule))
      (and (= ?r:rank ?rank) (eq ?r:conclusion ?goal))))
    (if (> (length$ ?matches) 0) then
      (bind ?rule (nth$ 1 ?matches))
      (bind ?name (fact-slot-value ?rule name))
      (assert (bc-event (depth ?depth) (message (str-cat "Пробуем " ?name))))
      (bind ?children (create$))
      (bind ?success TRUE)
      (foreach ?condition (fact-slot-value ?rule conditions)
        (bind ?child (prove-goal ?condition (expand$ ?path) ?goal))
        (if (= ?child 0) then
          (assert (bc-event (depth ?depth)
            (message (str-cat ?name ": не доказано " ?condition))))
          (bind ?success FALSE)
          (break))
        (bind ?children (create$ ?children ?child)))
      (if ?success then
        (assert (bc-event (depth ?depth)
          (message (str-cat "Доказано правилом " ?name))))
        (return (fact-index (assert (bc-proof
          (goal ?goal) (rule ?name) (children ?children))))))))
  (assert (bc-event (depth ?depth) (message (str-cat "Не доказано: " ?goal))))
  (return 0))
