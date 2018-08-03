#pragma once

template <typename T1, typename T2>
bool isIn(const T1& object,const T2& container) {
    for(auto obj : container){
        if(obj==object){return 1;}
    }
    return 0;
}