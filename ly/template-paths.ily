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

#(define-public ekm-font-paths '(
  "{1}"
{2}))

#(define-public (ekm-path-stencil cp size thickness filled)
  (let ((path (assv-ref (cdr ekm-font-paths) cp))
        (s (/ (magstep size) 256)))
    (if path
      (make-path-stencil path (* thickness s) s s filled)
      empty-stencil)))

#(define-markup-command (ekm-path layout props cp)
  (integer?)
  #:properties ((font-size 0)
                (thickness 0)
                (filled #t))
  (ekm-path-stencil cp font-size thickness filled))
