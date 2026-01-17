%% Copyright {0}
%%
%% This program is free software: you can redistribute it and/or modify
%% it under the terms of the GNU General Public License as published by
%% the Free Software Foundation, either version 3 of the License, or
%% (at your option) any later version.
%%
%% This program is distributed in the hope that it will be useful,
%% but WITHOUT ANY WARRANTY; without even the implied warranty of
%% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%% GNU General Public License at <http://www.gnu.org/licenses/>
%% for more details.
%%

\version "2.22.0"

#(define-public ekm-font-map '(
  "{1}"
{2}))

#(define-markup-command (ekm-glyph layout props name)
  (string?)
  #:properties ((font-size 0))
  (let ((cp (assoc-ref (cdr ekm-font-map) name)))
    (if cp
      (interpret-markup layout
        (cons
          `((font-size . ,(+ font-size 5))
            (font-name . ,(car ekm-font-map)))
          props)
        (ly:wide-char->utf-8 cp))
      (interpret-markup layout props
        (make-musicglyph-markup name)))))

#(define-public (ekm-has-glyph? name)
   (pair? (assoc name (cdr ekm-font-map))))

#(define-public (ekm-glyphname code)
  (let name ((l (cdr ekm-font-map)))
    (if (null? l)
      #f (if (= code (cdar l)) (caar l) (name (cdr l))))))
