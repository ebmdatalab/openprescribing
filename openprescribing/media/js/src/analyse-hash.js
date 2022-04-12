import _ from "underscore";

const hashHelper = {
  getHashParams() {
    const hashParams = {};
    let e;
    const a = /\+/g;
    const r = /([^&;=]+)=?([^&;]*)/g;

    const d = (s) => {
      if (typeof s === "string") {
        if (s === "true") {
          return true;
        } else if (s === "false") {
          return false;
        } else {
          return decodeURIComponent(s.replace(a, " "));
        }
      } else {
        return s.map((e) => decodeURIComponent(e.replace(a, " ")));
      }
    };

    const hash = window.location.hash.substring(1);
    while ((e = r.exec(hash))) {
      let key = e[1];
      if (key === "numerator") {
        key = "num";
      }
      if (key === "denominator") {
        key = "denom";
      }
      if (key === "numeratorIds") {
        key = "numIds";
      }
      if (key === "denominatorIds") {
        key = "denomIds";
      }
      let val = e[2];
      val = val.replace(/,\s*$/, "");
      if (key === "orgIds" || key === "numIds" || key === "denomIds") {
        hashParams[d(key)] = $.map(val.split(","), (v) => {
          if (d(v) !== "") {
            return {
              id: d(v),
            };
          }
        });
      } else {
        hashParams[d(key)] = d(val);
      }
    }
    // console.log('getHashParams', hashParams);
    return hashParams;
  },

  setHashParams(params) {
    // console.log('setHashParams', params);
    let hash = "";
    for (const k in params) {
      if (k === "orgIds" || k === "numIds" || k === "denomIds") {
        if (params[k].length > 0) {
          hash += `${k}=`;
          _.each(params[k], ({ id }, i) => {
            hash += id;
            if (i !== params[k].length - 1) {
              hash += ",";
            }
          });
          hash += "&";
        }
      } else if (
        k === "hideOutliers" ||
        k === "num" ||
        k === "denom" ||
        k === "org" ||
        k === "selectedTab"
      ) {
        if (params[k] !== "chemical") {
          hash += `${k}=${params[k]}&`;
        }
      }
    }
    hash = hash.replace(/&$/, "");
    window.location.hash = hash;
    return hash;
  },
};

export default hashHelper;
